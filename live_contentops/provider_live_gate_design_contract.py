"""Provider documentation review + Telegram one-request architecture design.

Tasks 0174TV (provider documentation review), 0174TW (Telegram capability map),
and 0174TX (Telegram one-request dispatch architecture design) -- one
deterministic, LOCAL design-authority batch on top of the accepted chain that
ends at the one-request supervised dispatch gate:

  * 0174TM/TN/TO + R1: kill switch + rate/spend/retry policy + one-request
    supervised dispatch gate producing a local ``DispatchAuthorizationCandidate``.
  * 0174TP/TQ/TR + R1: redacted immutable audit ledger + operator live-gate
    readiness review + live-gate decision packet.
  * 0174TS/TT/TU + R1: operator live-gate policy dry-run + checklist packet +
    documentation/state sync packet.

Product role of this batch (all LOCAL, all deterministic, DESIGN ONLY):
  1. 0174TV records a structured review of the OFFICIAL provider documentation
     (Telegram Bot API) as the single source of truth. It captures only the
     verified, non-secret facts needed to design a supervised one-request send:
     the API host, the method-invocation shape, the supervised send method, the
     read-only identity method, and the inbound methods this product does NOT
     use. It performs NO network fetch; the operator supplies the reviewed facts
     and this contract canonicalizes + fingerprints them.
  2. 0174TW builds a ``TelegramCapabilityMap`` binding the supervised single
     post to EXACTLY one method (``sendMessage``) with its documented required
     parameters, an explicit optional-parameter allow-list, and the hard
     platform constraints (text length bound, parse-mode allow-list, UTF-8).
     It records that long-polling and webhook receiving are mutually exclusive
     and that NEITHER is used by a one-shot supervised send.
  3. 0174TX designs the future one-request dispatch path: the credential-handle
     boundary (a credential is referenced ONLY by a symbolic handle id and is
     never hydrated here), the payload-hash binding, the fail-closed posture,
     and the requirement of a separate operator-owned live gate. It consumes an
     upstream dispatch-authorization candidate / audit and re-derives unsafe
     behavior from the flags. It produces a ``ProviderLiveGateDesign`` that is
     explicitly NOT a dispatch, NOT live-executable, and NOT a credential
     hydration.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no urllib request
    clients, no socket/ssl/http server, no selenium/playwright, no
    dotenv/keyring/sqlite, no openai/anthropic/telegram/tweepy SDKs.
  * NO network call of any kind. The provider documentation is REVIEWED by the
    operator and supplied as facts; this module never fetches it.
  * NO env / .env / keyring / browser-session / credential-file read.
  * NO OAuth, token exchange/refresh, credential hydration.
  * NO live posting, sendMessage call, platform API call, dispatch, scheduler,
    retry loop, autonomous replies/DMs, scraping, or runtime.
  * Raw chat id / username / phone / token / bot token / webhook url / raw
    provider response / profile url are rejected or redacted by a fail-closed
    scanner and never persisted. Provider method/parameter NAMES are symbolic
    documentation vocabulary, never secret material.
  * NO financial advice framing in any design text fails closed.
  * A design is NEVER dispatch and NEVER live readiness; the operator-owned
    live gate remains a separate future task. Missing/ambiguous/unsafe inputs
    block (fail closed).

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path

# Upstream authority layers. This batch CONSUMES their outputs; it never
# bypasses them. The redaction + financial-advice scanners are reused as the
# single source of truth.
from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import editorial_preview_supervised_dry_run_contract as editorial

TASK_LABEL = (
    "TASK_CONTENTOPS_0174TV_TW_TX_CORE_PROVIDER_DOC_REVIEW_AND_TELEGRAM_ONE_"
    "REQUEST_ARCHITECTURE_BATCH_V0"
)
MODEL = "PROVIDER_LIVE_GATE_DESIGN_CONTRACT_0174TV_TW_TX"
MODEL_VERSION = "0174TV_TW_TX_PROVIDER_LIVE_GATE_DESIGN_V1"

PROVIDER_DOC_REVIEW_SCHEMA = "contentops.provider_documentation_review"
PROVIDER_DOC_REVIEW_SCHEMA_VERSION = "0174TV_PROVIDER_DOCUMENTATION_REVIEW_V1"
CAPABILITY_MAP_SCHEMA = "contentops.telegram_capability_map"
CAPABILITY_MAP_SCHEMA_VERSION = "0174TW_TELEGRAM_CAPABILITY_MAP_V1"
CREDENTIAL_BOUNDARY_SCHEMA = "contentops.credential_boundary_design"
CREDENTIAL_BOUNDARY_SCHEMA_VERSION = "0174TX_CREDENTIAL_BOUNDARY_DESIGN_V1"
ARCHITECTURE_SCHEMA = "contentops.telegram_one_request_architecture_design"
ARCHITECTURE_SCHEMA_VERSION = "0174TX_TELEGRAM_ONE_REQUEST_ARCHITECTURE_V1"
DESIGN_SCHEMA = "contentops.provider_live_gate_design"
DESIGN_SCHEMA_VERSION = "0174TV_TW_TX_PROVIDER_LIVE_GATE_DESIGN_V1"

SOURCE_BASELINE_COMMIT = "39de54ae8d0bc01fa5d0afc4a99e47efbec899a3"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174TV_TW_TX")
PACKET_FILENAME = "provider_live_gate_design_contract_packet.json"
DOC_FILENAME = "provider_live_gate_design_contract.md"

NEXT_REQUIRED_GATE = (
    "an operator-owned live gate that hydrates the Telegram bot credential "
    "handle ONCE, performs a single read-only identity check, and then "
    "performs EXACTLY one supervised send for an already-approved payload "
    "hash; credential hydration and any live platform call remain separate "
    "future operator-owned gates and are NOT enabled here"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TY_TZ_UA_TELEGRAM_CREDENTIAL_HANDLE_BOUNDARY_AND_"
    "READ_ONLY_IDENTITY_PROOF_DESIGN_BATCH_V0"
)


# --------------------------------------------------------------------------- #
# Status vocabularies (symbolic only)
# --------------------------------------------------------------------------- #
class Status:
    PASS = "pass"
    BLOCKED = "blocked"
    FAIL_CLOSED = "fail_closed"


# Provider identity.
PROVIDER_TELEGRAM = "telegram"

# Official, non-secret documentation facts (verified by operator review).
# NOTE: the host is recorded WITHOUT the "/bot" credential path on purpose so
# no raw bot-token URL shape is ever persisted. The path template references
# the credential ONLY by a symbolic handle placeholder.
TELEGRAM_API_HOST = "api.telegram.org"
TELEGRAM_DOC_SOURCE_URL = "https://core.telegram.org/bots/api"
TELEGRAM_METHOD_PATH_TEMPLATE = "/{redacted_credential_handle}/{method_name}"

# Supervised one-request method + read-only identity method (documentation
# vocabulary -- these are method NAMES, never calls).
METHOD_SUPERVISED_SEND = "sendMessage"
METHOD_READ_ONLY_IDENTITY = "getMe"

# Inbound-receiving methods this product does NOT use for a one-shot send.
# Long polling and webhook receiving are mutually exclusive per the docs; a
# one-request supervised send uses NEITHER.
INBOUND_METHODS_NOT_USED = ("getUpdates", "setWebhook")

# Hard platform constraints for the supervised send (verified facts).
TELEGRAM_MAX_TEXT_LENGTH = 4096
TELEGRAM_MIN_TEXT_LENGTH = 1
PARSE_MODE_OPTIONS = ("HTML", "MarkdownV2", "Markdown")

# Documented sendMessage parameters this design recognises. These are
# documentation NAMES (a schema vocabulary), never values.
SUPERVISED_SEND_REQUIRED_PARAMS = ("chat_id", "text")
SUPERVISED_SEND_OPTIONAL_PARAMS = (
    "parse_mode",
    "entities",
    "link_preview_options",
    "disable_notification",
    "protect_content",
    "message_thread_id",
    "reply_parameters",
    "reply_markup",
)

# Outcome classes.
DOC_REVIEW_RECORDED = "provider_documentation_review_recorded_not_dispatch"
DOC_REVIEW_BLOCKED = "provider_documentation_review_blocked"
DOC_REVIEW_FAIL_CLOSED = "provider_documentation_review_fail_closed_forbidden_value"

CAPABILITY_MAP_BUILT = "telegram_capability_map_built_not_dispatch"
CAPABILITY_MAP_BLOCKED = "telegram_capability_map_blocked"
CAPABILITY_MAP_FAIL_CLOSED = "telegram_capability_map_fail_closed_forbidden_value"

DESIGN_RECORDED = "provider_live_gate_design_recorded_not_dispatch"
DESIGN_BLOCKED = "provider_live_gate_design_blocked"
DESIGN_FAIL_CLOSED = "provider_live_gate_design_fail_closed_forbidden_value"

# Blocked-reason classes.
BLOCK_FORBIDDEN_VALUE = "design_forbidden_value_detected"
BLOCK_FINANCIAL_ADVICE = "design_financial_advice_detected"
BLOCK_DOC_SOURCE_MISSING = "provider_doc_source_missing"
BLOCK_DOC_SOURCE_NOT_OFFICIAL = "provider_doc_source_not_official"
BLOCK_PROVIDER_NOT_SUPPORTED = "provider_not_supported"
BLOCK_REVIEWER_MISSING = "reviewer_operator_id_missing"
BLOCK_METHOD_NOT_SUPERVISED_SEND = "method_is_not_supervised_send"
BLOCK_REQUIRED_PARAM_MISSING = "supervised_send_required_param_missing"
BLOCK_OPTIONAL_PARAM_NOT_ALLOWLISTED = "supervised_send_optional_param_not_allowlisted"
BLOCK_PARSE_MODE_NOT_ALLOWLISTED = "parse_mode_not_allowlisted"
BLOCK_TEXT_LENGTH_OUT_OF_BOUNDS = "text_length_out_of_documented_bounds"
BLOCK_INBOUND_RECEIVING_USED = "inbound_receiving_method_used"
BLOCK_CREDENTIAL_HANDLE_MISSING = "credential_handle_id_missing"
BLOCK_DOC_REVIEW_NOT_RECORDED = "provider_doc_review_not_recorded"
BLOCK_CAPABILITY_MAP_NOT_BUILT = "telegram_capability_map_not_built"
BLOCK_CANDIDATE_NOT_CREATED = "dispatch_authorization_candidate_not_created"
BLOCK_MISSING_FIELD = "design_required_field_missing"

# R1-style upstream unsafe-behavior revalidation reasons.
BLOCK_CANDIDATE_UNSAFE_BEHAVIOR = "design_candidate_unsafe_behavior_claimed"
BLOCK_DOC_REVIEW_UNSAFE_BEHAVIOR = "design_doc_review_unsafe_behavior_claimed"
BLOCK_CAPABILITY_MAP_UNSAFE_BEHAVIOR = "design_capability_map_unsafe_behavior_claimed"

# Artifact-name labels passed to detect_unsafe_behavior_claims.
ARTIFACT_CANDIDATE = "candidate"
ARTIFACT_DOC_REVIEW = "doc_review"
ARTIFACT_CAPABILITY_MAP = "capability_map"

_ARTIFACT_UNSAFE_BASE = {
    ARTIFACT_CANDIDATE: BLOCK_CANDIDATE_UNSAFE_BEHAVIOR,
    ARTIFACT_DOC_REVIEW: BLOCK_DOC_REVIEW_UNSAFE_BEHAVIOR,
    ARTIFACT_CAPABILITY_MAP: BLOCK_CAPABILITY_MAP_UNSAFE_BEHAVIOR,
}

# Universal unsafe-behavior flags that MUST be False on every consumed artifact.
_UNSAFE_BEHAVIOR_FLAGS = (
    "dispatch_performed",
    "live_request_performed",
    "platform_api_called",
    "telegram_api_called",
    "credential_hydrated",
    "llm_behavior",
    "network_performed",
    "scheduler_enabled",
    "auto_retry_allowed",
    "autonomous_reply_performed",
    "dispatch_ready",
    "live_ready",
)

# Design-specific readiness booleans that MUST be False where present.
_UNSAFE_READINESS_FLAGS = (
    "design_is_dispatch",
    "design_is_live_readiness",
    "design_is_credential_hydration",
    "design_is_provider_authorization",
    "valid_for_live_execution",
)


# --------------------------------------------------------------------------- #
# Redaction + financial-advice scanning + deterministic serialization.
# --------------------------------------------------------------------------- #
def scan_for_leaks(obj):
    """Return a sorted list of redaction violations (delegates to 0174ED)."""
    return approval.scan_for_leaks(obj)


def scan_for_financial_advice(obj):
    """Return a sorted list of financial-advice violations (delegates 0174TL)."""
    return editorial.scan_for_financial_advice(obj)


def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Shared safety flags
# --------------------------------------------------------------------------- #
def _safety_flags():
    """Hard-coded safety invariants attached to every 0174TV/TW/TX object."""
    return {
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "telegram_api_called": False,
        "credential_hydrated": False,
        "llm_behavior": False,
        "network_performed": False,
        "scheduler_enabled": False,
        "auto_retry_allowed": False,
        "autonomous_reply_performed": False,
        "dispatch_ready": False,
        "live_ready": False,
        "no_financial_advice_emitted": True,
    }


def detect_unsafe_behavior_claims(obj, artifact_name):
    """Return deterministic blocked reasons for any unsafe flag an artifact claims.

    A consumed upstream artifact (a dispatch-authorization candidate / audit, a
    provider documentation review, or a Telegram capability map) must NOT be
    able to carry a tampered flag claiming live/network/credential/scheduler/
    retry/dispatch behavior past this design contract just because its status
    metadata still reads clear. This helper re-derives the truth directly from
    the flags.

    A universal flag "claims" unsafe behavior when it is present and not False.
    A design-specific readiness boolean likewise blocks when present and not
    False. Returns a sorted, de-duplicated list whose first element (when any
    flag trips) is the artifact's bare unsafe-behavior-claimed class, followed
    by ``<base>:<flag>`` entries. An empty list means no unsafe behavior.
    """
    o = obj or {}
    base = _ARTIFACT_UNSAFE_BASE.get(
        artifact_name,
        "design_" + str(artifact_name) + "_unsafe_behavior_claimed")
    hits = []
    for flag in (_UNSAFE_BEHAVIOR_FLAGS + _UNSAFE_READINESS_FLAGS):
        if flag in o and o.get(flag) is not False:
            hits.append(flag)
    if not hits:
        return []
    reasons = [base]
    reasons.extend(base + ":" + flag for flag in hits)
    return sorted(set(reasons))


# --------------------------------------------------------------------------- #
# 0174TV: Provider documentation review
# --------------------------------------------------------------------------- #
def review_provider_documentation(*, provider, reviewer_operator_id,
                                  doc_source_url=TELEGRAM_DOC_SOURCE_URL,
                                  api_host=TELEGRAM_API_HOST,
                                  reviewed_at_epoch=None):
    """Record a deterministic review of the OFFICIAL provider documentation.

    Fail-closed. This performs NO network fetch: the operator has reviewed the
    official docs and the verified, non-secret facts are canonicalized here.
    Only Telegram is supported in this batch. Returns a redaction-clean
    ProviderDocumentationReview pure value.

      * forbidden credential/provider material => ``fail_closed``;
      * a missing/unofficial doc source blocks;
      * an unsupported provider blocks;
      * a missing reviewer operator id blocks.
    """
    blocked = []

    scan_payload = {
        "provider": provider,
        "reviewer_operator_id": reviewer_operator_id,
        "doc_source_url": doc_source_url,
        "api_host": api_host,
    }
    if scan_for_leaks(scan_payload):
        return _doc_review_result(
            DOC_REVIEW_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE],
            recorded=False, forbidden_detected=True, provider=provider,
            reviewer_operator_id=reviewer_operator_id,
            doc_source_url=doc_source_url, api_host=api_host)

    if provider != PROVIDER_TELEGRAM:
        blocked.append(BLOCK_PROVIDER_NOT_SUPPORTED)

    if not doc_source_url:
        blocked.append(BLOCK_DOC_SOURCE_MISSING)
    elif not str(doc_source_url).startswith("https://core.telegram.org/"):
        blocked.append(BLOCK_DOC_SOURCE_NOT_OFFICIAL)

    if not reviewer_operator_id:
        blocked.append(BLOCK_REVIEWER_MISSING)

    recorded = not blocked
    outcome = DOC_REVIEW_RECORDED if recorded else DOC_REVIEW_BLOCKED
    return _doc_review_result(
        outcome, blocked=sorted(set(blocked)), recorded=recorded,
        forbidden_detected=False, provider=provider,
        reviewer_operator_id=reviewer_operator_id,
        doc_source_url=doc_source_url, api_host=api_host,
        reviewed_at_epoch=reviewed_at_epoch)


def _doc_review_result(outcome_class, *, blocked, recorded, forbidden_detected,
                       provider, reviewer_operator_id, doc_source_url, api_host,
                       reviewed_at_epoch=None):
    """Build a deterministic ProviderDocumentationReview (pure value)."""
    status = (Status.PASS if recorded
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "provider_doc_review_schema": PROVIDER_DOC_REVIEW_SCHEMA,
        "provider_doc_review_schema_version": PROVIDER_DOC_REVIEW_SCHEMA_VERSION,
        "status": status,
        "provider_doc_review_outcome_class": outcome_class,
        "provider_doc_review_recorded": recorded,
        "provider": provider,
        "reviewer_operator_id": reviewer_operator_id,
        "doc_source_url": doc_source_url,
        "doc_source_is_official": (
            bool(doc_source_url)
            and str(doc_source_url).startswith("https://core.telegram.org/")),
        "api_host": api_host,
        "method_path_template": TELEGRAM_METHOD_PATH_TEMPLATE,
        "reviewed_at_epoch": (int(reviewed_at_epoch)
                              if reviewed_at_epoch is not None else None),
        # Verified, non-secret documentation facts.
        "supervised_send_method": METHOD_SUPERVISED_SEND,
        "read_only_identity_method": METHOD_READ_ONLY_IDENTITY,
        "inbound_methods_not_used": list(INBOUND_METHODS_NOT_USED),
        "methods_case_insensitive": True,
        "transport_is_https_only": True,
        "encoding_is_utf8": True,
        "inbound_receiving_used": False,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- a doc review is NEVER a fetch / dispatch / live.
        **_safety_flags(),
        "doc_review_performed_network_fetch": False,
        "design_is_dispatch": False,
        "design_is_live_readiness": False,
    }
    result["provider_doc_review_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# 0174TW: Telegram capability map
# --------------------------------------------------------------------------- #
def build_telegram_capability_map(doc_review, *, requested_optional_params=(),
                                  requested_parse_mode="HTML",
                                  planned_text_length=None):
    """Build a deterministic TelegramCapabilityMap binding the supervised send.

    Fail-closed. The supervised single post maps to EXACTLY one method
    (``sendMessage``). Blocks when:

      * forbidden credential/provider material => ``fail_closed``;
      * the doc review is not recorded;
      * a requested optional param is not on the documented allow-list;
      * a requested parse mode is not on the documented allow-list;
      * a planned text length is outside the documented [1, 4096] bound;
      * any inbound-receiving method is requested.
    """
    dr = doc_review or {}
    blocked = []

    scan_payload = {
        "requested_optional_params": list(requested_optional_params or ()),
        "requested_parse_mode": requested_parse_mode,
    }
    if scan_for_leaks([dr, scan_payload]):
        return _capability_map_result(
            CAPABILITY_MAP_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE],
            built=False, forbidden_detected=True, doc_review=dr,
            optional_params=[], parse_mode=requested_parse_mode,
            planned_text_length=planned_text_length)

    if not _doc_review_is_recorded(dr):
        blocked.append(BLOCK_DOC_REVIEW_NOT_RECORDED)

    # R1: a "recorded"/pass doc review must not smuggle unsafe behavior.
    blocked.extend(detect_unsafe_behavior_claims(dr, ARTIFACT_DOC_REVIEW))

    optional_params = [str(p) for p in (requested_optional_params or ())]
    for p in optional_params:
        if p in INBOUND_METHODS_NOT_USED:
            blocked.append(BLOCK_INBOUND_RECEIVING_USED)
        if p not in SUPERVISED_SEND_OPTIONAL_PARAMS:
            blocked.append(BLOCK_OPTIONAL_PARAM_NOT_ALLOWLISTED + ":" + p)

    if requested_parse_mode is not None and (
            requested_parse_mode not in PARSE_MODE_OPTIONS):
        blocked.append(BLOCK_PARSE_MODE_NOT_ALLOWLISTED)

    if planned_text_length is not None:
        if (int(planned_text_length) < TELEGRAM_MIN_TEXT_LENGTH
                or int(planned_text_length) > TELEGRAM_MAX_TEXT_LENGTH):
            blocked.append(BLOCK_TEXT_LENGTH_OUT_OF_BOUNDS)

    built = not blocked
    outcome = CAPABILITY_MAP_BUILT if built else CAPABILITY_MAP_BLOCKED
    return _capability_map_result(
        outcome, blocked=sorted(set(blocked)), built=built,
        forbidden_detected=False, doc_review=dr,
        optional_params=optional_params, parse_mode=requested_parse_mode,
        planned_text_length=planned_text_length)


def _capability_map_result(outcome_class, *, blocked, built, forbidden_detected,
                           doc_review, optional_params, parse_mode,
                           planned_text_length):
    """Build a deterministic TelegramCapabilityMap (pure value)."""
    status = (Status.PASS if built
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    dr = doc_review or {}
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "capability_map_schema": CAPABILITY_MAP_SCHEMA,
        "capability_map_schema_version": CAPABILITY_MAP_SCHEMA_VERSION,
        "status": status,
        "capability_map_outcome_class": outcome_class,
        "capability_map_built": built,
        "provider": dr.get("provider"),
        "supervised_send_method": METHOD_SUPERVISED_SEND,
        "read_only_identity_method": METHOD_READ_ONLY_IDENTITY,
        "required_param_names": list(SUPERVISED_SEND_REQUIRED_PARAMS),
        "optional_param_allowlist": list(SUPERVISED_SEND_OPTIONAL_PARAMS),
        "requested_optional_param_names": sorted(set(optional_params)),
        "parse_mode_allowlist": list(PARSE_MODE_OPTIONS),
        "requested_parse_mode": parse_mode,
        "min_text_length": TELEGRAM_MIN_TEXT_LENGTH,
        "max_text_length": TELEGRAM_MAX_TEXT_LENGTH,
        "planned_text_length": (int(planned_text_length)
                                if planned_text_length is not None else None),
        "inbound_methods_not_used": list(INBOUND_METHODS_NOT_USED),
        "inbound_receiving_used": False,
        "long_polling_and_webhook_mutually_exclusive": True,
        "max_requests_authorized_by_design": 1,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- a capability map is NEVER dispatch / live.
        **_safety_flags(),
        "design_is_dispatch": False,
        "design_is_live_readiness": False,
        "design_is_provider_authorization": False,
    }
    result["capability_map_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# 0174TX: Credential boundary + one-request architecture design
# --------------------------------------------------------------------------- #
def design_credential_boundary(*, credential_handle_id,
                               destination_binding_id):
    """Design the credential-handle boundary (pure value, no hydration).

    A credential is referenced ONLY by a symbolic handle id; the destination is
    referenced ONLY by a symbolic binding id. NOTHING is hydrated, fetched, or
    resolved to a raw value here.
    """
    return {
        "credential_boundary_schema": CREDENTIAL_BOUNDARY_SCHEMA,
        "credential_boundary_schema_version": CREDENTIAL_BOUNDARY_SCHEMA_VERSION,
        "credential_handle_id": credential_handle_id,
        "destination_binding_id": destination_binding_id,
        "credential_referenced_by_handle_only": True,
        "credential_hydrated": False,
        "credential_hydration_is_future_operator_gate": True,
        "raw_credential_persisted": False,
        "destination_referenced_by_binding_only": True,
    }


def _doc_review_is_recorded(doc_review):
    dr = doc_review or {}
    return (
        dr.get("provider_doc_review_outcome_class") == DOC_REVIEW_RECORDED
        and dr.get("provider_doc_review_recorded") is True
        and dr.get("status") == Status.PASS
    )


def _capability_map_is_built(capability_map):
    cm = capability_map or {}
    return (
        cm.get("capability_map_outcome_class") == CAPABILITY_MAP_BUILT
        and cm.get("capability_map_built") is True
        and cm.get("status") == Status.PASS
    )


def _candidate_is_created(candidate_audit):
    """True if the upstream object is a created (not duplicate) candidate audit.

    Accepts either a 0174TO redacted immutable dispatch audit (which carries
    ``candidate_created_not_dispatched``) or the gate result that embeds it.
    """
    c = candidate_audit or {}
    if c.get("candidate_created_not_dispatched") is True:
        return True
    inner = c.get("dispatch_authorization_candidate")
    if isinstance(inner, dict):
        return inner.get("max_requests_authorized") == 1
    return False


def build_provider_live_gate_design(doc_review, capability_map,
                                    candidate_audit, *,
                                    credential_handle_id,
                                    destination_binding_id,
                                    payload_hash_short=None,
                                    design_operator_id=None):
    """Produce a deterministic ProviderLiveGateDesign or block. Fail-closed.

    Re-proves the full local design authority. The result is
    ``provider_live_gate_design_blocked`` unless ALL hold:

      * no forbidden credential/provider material and no financial advice;
      * the provider documentation review is recorded;
      * the Telegram capability map is built;
      * the upstream dispatch-authorization candidate was created (one request);
      * none of the consumed artifacts claims unsafe behavior (R1 revalidation);
      * a credential handle id is present.

    Even when all hold, the design is ``..._recorded_not_dispatch`` and is
    explicitly NOT live-executable, NOT a dispatch, and NOT a credential
    hydration. It always ``requires_operator_live_gate``.
    """
    dr = doc_review or {}
    cm = capability_map or {}
    ca = candidate_audit or {}
    blocked = []

    scan_payload = {
        "credential_handle_id": credential_handle_id,
        "destination_binding_id": destination_binding_id,
        "payload_hash_short": payload_hash_short,
        "design_operator_id": design_operator_id,
    }
    if scan_for_leaks([dr, cm, ca, scan_payload]):
        return _design_result(
            DESIGN_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE],
            recorded=False, forbidden_detected=False, financial_detected=False,
            doc_review=dr, capability_map=cm, candidate_audit=ca,
            credential_handle_id=credential_handle_id,
            destination_binding_id=destination_binding_id,
            payload_hash_short=payload_hash_short,
            design_operator_id=design_operator_id,
            forbidden_or_financial=True)

    if scan_for_financial_advice([dr, cm, ca, scan_payload]):
        return _design_result(
            DESIGN_FAIL_CLOSED, blocked=[BLOCK_FINANCIAL_ADVICE],
            recorded=False, forbidden_detected=False, financial_detected=True,
            doc_review=dr, capability_map=cm, candidate_audit=ca,
            credential_handle_id=credential_handle_id,
            destination_binding_id=destination_binding_id,
            payload_hash_short=payload_hash_short,
            design_operator_id=design_operator_id,
            forbidden_or_financial=True)

    if not _doc_review_is_recorded(dr):
        blocked.append(BLOCK_DOC_REVIEW_NOT_RECORDED)
    if not _capability_map_is_built(cm):
        blocked.append(BLOCK_CAPABILITY_MAP_NOT_BUILT)
    if not _candidate_is_created(ca):
        blocked.append(BLOCK_CANDIDATE_NOT_CREATED)
    if not credential_handle_id:
        blocked.append(BLOCK_CREDENTIAL_HANDLE_MISSING)

    # R1 upstream safety-flag revalidation across every consumed artifact.
    blocked.extend(detect_unsafe_behavior_claims(dr, ARTIFACT_DOC_REVIEW))
    blocked.extend(detect_unsafe_behavior_claims(cm, ARTIFACT_CAPABILITY_MAP))
    blocked.extend(detect_unsafe_behavior_claims(ca, ARTIFACT_CANDIDATE))

    recorded = not blocked
    outcome = DESIGN_RECORDED if recorded else DESIGN_BLOCKED
    return _design_result(
        outcome, blocked=sorted(set(blocked)), recorded=recorded,
        forbidden_detected=False, financial_detected=False,
        doc_review=dr, capability_map=cm, candidate_audit=ca,
        credential_handle_id=credential_handle_id,
        destination_binding_id=destination_binding_id,
        payload_hash_short=payload_hash_short,
        design_operator_id=design_operator_id, forbidden_or_financial=False)


def _design_result(outcome_class, *, blocked, recorded, forbidden_detected,
                   financial_detected, doc_review, capability_map,
                   candidate_audit, credential_handle_id,
                   destination_binding_id, payload_hash_short,
                   design_operator_id, forbidden_or_financial):
    """Build a deterministic ProviderLiveGateDesign (pure value)."""
    if forbidden_or_financial:
        status = Status.FAIL_CLOSED
    elif recorded:
        status = Status.PASS
    else:
        status = Status.BLOCKED
    dr = doc_review or {}
    cm = capability_map or {}
    ca = candidate_audit or {}

    boundary = design_credential_boundary(
        credential_handle_id=credential_handle_id,
        destination_binding_id=destination_binding_id)

    architecture = {
        "architecture_schema": ARCHITECTURE_SCHEMA,
        "architecture_schema_version": ARCHITECTURE_SCHEMA_VERSION,
        "provider": PROVIDER_TELEGRAM,
        "api_host": TELEGRAM_API_HOST,
        "method_path_template": TELEGRAM_METHOD_PATH_TEMPLATE,
        "supervised_send_method": METHOD_SUPERVISED_SEND,
        "read_only_identity_method": METHOD_READ_ONLY_IDENTITY,
        "request_count_authorized_by_design": 1,
        "transport_is_https_only": True,
        "encoding_is_utf8": True,
        "inbound_receiving_used": False,
        "payload_hash_short": payload_hash_short,
        # Ordered design steps for the FUTURE operator-owned live gate.
        "future_live_gate_step_order": [
            "operator_hydrates_credential_handle_once",
            "operator_runs_read_only_identity_check",
            "operator_confirms_approved_payload_hash_binding",
            "operator_authorizes_exactly_one_supervised_send",
            "record_redacted_immutable_audit",
        ],
    }

    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "design_schema": DESIGN_SCHEMA,
        "design_schema_version": DESIGN_SCHEMA_VERSION,
        "status": status,
        "provider_live_gate_design_outcome_class": outcome_class,
        "provider_live_gate_design_recorded": recorded,
        "provider": PROVIDER_TELEGRAM,
        "design_operator_id": design_operator_id,
        "provider_doc_review_outcome_class": dr.get(
            "provider_doc_review_outcome_class"),
        "capability_map_outcome_class": cm.get("capability_map_outcome_class"),
        "candidate_created_not_dispatched": _candidate_is_created(ca),
        "credential_boundary": boundary,
        "architecture": architecture,
        "payload_hash_short": payload_hash_short,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_detected,
        "requires_operator_live_gate": True,
        # Hard invariants -- a design is NEVER dispatch / live / hydration.
        **_safety_flags(),
        "design_is_dispatch": False,
        "design_is_live_readiness": False,
        "design_is_credential_hydration": False,
        "design_is_provider_authorization": False,
        "valid_for_live_execution": False,
        "no_raw_credential_stored": True,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    result["provider_live_gate_design_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# Deterministic packet + doc builders + explicit artifact writer
# --------------------------------------------------------------------------- #
def build_packet():
    """Return a deterministic, redaction-clean contract packet (pure value)."""
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": Status.PASS,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "provider_doc_review_schema": PROVIDER_DOC_REVIEW_SCHEMA,
        "provider_doc_review_schema_version": PROVIDER_DOC_REVIEW_SCHEMA_VERSION,
        "capability_map_schema": CAPABILITY_MAP_SCHEMA,
        "capability_map_schema_version": CAPABILITY_MAP_SCHEMA_VERSION,
        "credential_boundary_schema": CREDENTIAL_BOUNDARY_SCHEMA,
        "credential_boundary_schema_version": CREDENTIAL_BOUNDARY_SCHEMA_VERSION,
        "architecture_schema": ARCHITECTURE_SCHEMA,
        "architecture_schema_version": ARCHITECTURE_SCHEMA_VERSION,
        "design_schema": DESIGN_SCHEMA,
        "design_schema_version": DESIGN_SCHEMA_VERSION,
        "provider": PROVIDER_TELEGRAM,
        "api_host": TELEGRAM_API_HOST,
        "doc_source_url": TELEGRAM_DOC_SOURCE_URL,
        "method_path_template": TELEGRAM_METHOD_PATH_TEMPLATE,
        "supervised_send_method": METHOD_SUPERVISED_SEND,
        "read_only_identity_method": METHOD_READ_ONLY_IDENTITY,
        "inbound_methods_not_used": list(INBOUND_METHODS_NOT_USED),
        "required_param_names": list(SUPERVISED_SEND_REQUIRED_PARAMS),
        "optional_param_allowlist": list(SUPERVISED_SEND_OPTIONAL_PARAMS),
        "parse_mode_allowlist": list(PARSE_MODE_OPTIONS),
        "min_text_length": TELEGRAM_MIN_TEXT_LENGTH,
        "max_text_length": TELEGRAM_MAX_TEXT_LENGTH,
        "doc_review_outcome_classes": [
            DOC_REVIEW_RECORDED, DOC_REVIEW_BLOCKED, DOC_REVIEW_FAIL_CLOSED,
        ],
        "capability_map_outcome_classes": [
            CAPABILITY_MAP_BUILT, CAPABILITY_MAP_BLOCKED,
            CAPABILITY_MAP_FAIL_CLOSED,
        ],
        "design_outcome_classes": [
            DESIGN_RECORDED, DESIGN_BLOCKED, DESIGN_FAIL_CLOSED,
        ],
        "r1_upstream_revalidation_blocked_reasons": [
            BLOCK_CANDIDATE_UNSAFE_BEHAVIOR,
            BLOCK_DOC_REVIEW_UNSAFE_BEHAVIOR,
            BLOCK_CAPABILITY_MAP_UNSAFE_BEHAVIOR,
        ],
        "r1_revalidated_unsafe_flags": list(
            _UNSAFE_BEHAVIOR_FLAGS + _UNSAFE_READINESS_FLAGS),
        "future_live_gate_step_order": [
            "operator_hydrates_credential_handle_once",
            "operator_runs_read_only_identity_check",
            "operator_confirms_approved_payload_hash_binding",
            "operator_authorizes_exactly_one_supervised_send",
            "record_redacted_immutable_audit",
        ],
        "hard_invariants": [
            "provider_documentation_is_official_source_of_truth",
            "documentation_review_performs_no_network_fetch",
            "supervised_post_maps_to_exactly_one_send_method",
            "long_polling_and_webhook_mutually_exclusive",
            "inbound_receiving_not_used_by_one_shot_send",
            "credential_referenced_by_handle_only",
            "design_is_not_dispatch",
            "design_is_not_live_readiness",
            "design_is_not_credential_hydration",
            "design_is_not_provider_authorization",
            "design_requires_operator_owned_live_gate",
            "unsafe_upstream_behavior_claim_blocks_design",
            "no_credential_hydration",
            "no_platform_api",
            "no_telegram_send",
            "no_network",
            "no_scheduler",
            "no_retries",
            "no_autonomous_posting",
            "no_financial_advice_or_signal_framing",
            "missing_ambiguous_or_unsafe_input_blocks",
        ],
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
        "safety_flags": _safety_flags(),
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    """Return a deterministic, redaction-clean markdown contract document."""
    packet = build_packet()
    required = "\n".join(
        f"  * `{p}`" for p in packet["required_param_names"])
    optional = "\n".join(
        f"  * `{p}`" for p in packet["optional_param_allowlist"])
    parse_modes = ", ".join(f"`{p}`" for p in packet["parse_mode_allowlist"])
    not_used = ", ".join(f"`{m}`" for m in packet["inbound_methods_not_used"])
    steps = "\n".join(
        f"  {i}. `{s}`"
        for i, s in enumerate(packet["future_live_gate_step_order"], start=1))
    hard = "\n".join(f"  * `{inv}`" for inv in packet["hard_invariants"])
    r1_reasons = "\n".join(
        f"  * `{r}`"
        for r in packet["r1_upstream_revalidation_blocked_reasons"])
    return (
        f"# 0174TV/TW/TX Provider Doc Review + Telegram One-Request Architecture"
        f"\n\n"
        f"Task: `{TASK_LABEL}`\n\n"
        f"Model: `{MODEL}` version `{MODEL_VERSION}`\n\n"
        f"Baseline commit: `{SOURCE_BASELINE_COMMIT}`\n\n"
        f"## Role\n\n"
        f"This batch is LOCAL, deterministic, and DESIGN ONLY. It performs NO "
        f"network fetch, NO live platform API call, NO Telegram send, NO LLM/"
        f"provider call, NO env/credential read, NO credential hydration, NO "
        f"scheduler, and NO auto retry. It NEVER dispatches.\n\n"
        f"## 0174TV Provider documentation review\n\n"
        f"The OFFICIAL Telegram Bot API documentation (`{TELEGRAM_DOC_SOURCE_URL}`) "
        f"is the single source of truth. The operator reviews it; this contract "
        f"canonicalizes and fingerprints only the verified, non-secret facts. "
        f"The API host is recorded as `{TELEGRAM_API_HOST}` and the credentialed "
        f"path is referenced ONLY by the symbolic template "
        f"`{TELEGRAM_METHOD_PATH_TEMPLATE}`.\n\n"
        f"## 0174TW Telegram capability map\n\n"
        f"The supervised single post maps to EXACTLY one method "
        f"(`{METHOD_SUPERVISED_SEND}`). The read-only identity method is "
        f"`{METHOD_READ_ONLY_IDENTITY}`. Inbound-receiving methods are NOT used "
        f"for a one-shot send ({not_used}); long polling and webhook receiving "
        f"are mutually exclusive.\n\n"
        f"Documented required parameters:\n\n{required}\n\n"
        f"Optional-parameter allow-list:\n\n{optional}\n\n"
        f"Parse-mode allow-list: {parse_modes}. Text length must be within "
        f"`[{packet['min_text_length']}, {packet['max_text_length']}]` "
        f"characters after entities parsing.\n\n"
        f"## 0174TX One-request architecture design\n\n"
        f"A credential is referenced ONLY by a symbolic handle id and is NEVER "
        f"hydrated here. The future operator-owned live gate step order is:\n\n"
        f"{steps}\n\n"
        f"## R1 upstream safety-flag revalidation\n\n"
        f"The design re-derives upstream safety truth directly from the flags "
        f"on the consumed documentation review, capability map, and dispatch-"
        f"authorization candidate. A `pass`/`recorded` status can NOT hide a "
        f"tampered claim of network/platform/Telegram/credential/LLM/scheduler/"
        f"retry/dispatch or live-readiness behavior; any such claim blocks the "
        f"design:\n\n{r1_reasons}\n\n"
        f"## Hard invariants\n\n{hard}\n\n"
        f"## Next required gate\n\n{NEXT_REQUIRED_GATE}\n\n"
        f"Exact next task: `{EXACT_NEXT_TASK_RECOMMENDATION}`\n\n"
        f"Packet checksum: `{packet['checksum_sha256']}`\n")


def write_artifacts(base_dir):
    """Write the packet JSON + markdown doc under ``base_dir``. Explicit only.

    Returns the list of written absolute paths. This is the ONLY function that
    performs filesystem writes; importing the module performs none.
    """
    out_dir = os.path.join(base_dir, DOC_REL_DIR)
    os.makedirs(out_dir, exist_ok=True)
    packet_path = os.path.join(out_dir, PACKET_FILENAME)
    doc_path = os.path.join(out_dir, DOC_FILENAME)
    with open(packet_path, "w", encoding="utf-8") as fh:
        fh.write(serialize(build_packet()))
    with open(doc_path, "w", encoding="utf-8") as fh:
        fh.write(build_doc())
    return [packet_path, doc_path]
