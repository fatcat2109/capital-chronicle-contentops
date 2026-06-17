"""Telegram local adapter skeleton + one-request builder (LOCAL, NOT LIVE).

Tasks 0174TY (local Telegram adapter skeleton + payload renderer), 0174TZ
(deterministic one-request object builder + capability enforcer), and 0174UA
(redacted future response shape + local adapter readiness classifier) -- one
deterministic, LOCAL core-platform batch on top of the accepted design chain
that ends at the provider live-gate design contract:

  * 0174TM/TN/TO + R1: kill switch + rate/spend/retry policy + one-request
    supervised dispatch gate producing a ``DispatchAuthorizationCandidate``.
  * 0174TP/TQ/TR + R1: redacted immutable audit ledger + operator live-gate
    readiness review + live-gate decision packet.
  * 0174TS/TT/TU + R1: operator live-gate policy dry-run + checklist + doc sync.
  * 0174TV/TW/TX: provider documentation review + Telegram capability map +
    one-request architecture design (``ProviderLiveGateDesign``).

Product role of this batch (all LOCAL, all deterministic, REAL CORE CODE but
NEVER LIVE):
  1. 0174TY ``TelegramRenderedPayload`` consumes an approved/safe text artifact,
     validates the documented text length bound [1, 4096], supports a symbolic
     ``parse_mode`` (HTML / MarkdownV2 / Markdown / none), keeps a preview text
     separate from the send text, and fails closed on financial-advice/signal
     framing and on raw credential/chat/webhook/token-like material.
  2. 0174TZ ``TelegramOneRequestObject`` builds a deterministic request object
     for a FUTURE ``sendMessage`` -- with NO URL containing a token, NO token
     value, NO raw chat id; the credential and destination are referenced ONLY
     by symbolic ids; the method is recorded as a symbolic method string;
     ``request_count_authorized`` is exactly 1; and no auto retry / scheduler /
     webhook / polling is present. ``TelegramAdapterCapabilityEnforcer`` allows
     ONLY the text-message one-request path and rejects inbound-receiving,
     media/edit/delete/reply automation, and non-allowlisted optional params.
  3. 0174UA ``RedactedTelegramResponseShape`` is a FUTURE-ONLY shape for a
     provider response that stores only redacted status/code/message-id classes
     plus request/response checksums and NEVER stores a raw provider response,
     raw chat id, raw token, raw URL, headers, or cookies. The local adapter
     readiness classifier returns ``telegram_local_adapter_ready_not_live`` /
     ``..._blocked`` / ``..._fail_closed_forbidden_value`` and NEVER
     ``live_ready`` or ``valid_for_live_execution``.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no urllib request
    clients, no socket/ssl/http server, no selenium/playwright, no
    dotenv/keyring/sqlite, no openai/anthropic/telegram/tweepy SDKs.
  * NO network call. NO env / .env / keyring / browser-session / credential
    read. NO OAuth, token exchange/refresh, credential hydration.
  * NO live posting, supervised-send call, platform API call, dispatch,
    scheduler, retry loop, autonomous replies/DMs, scraping, or runtime.
  * Raw chat id / username / phone / token / bot token / webhook url / raw
    provider response / profile url / header / cookie are rejected or redacted
    by a fail-closed scanner and never persisted. Provider method/parameter
    NAMES are symbolic documentation vocabulary, never secret material.
  * NO financial advice / signal framing in any rendered text fails closed.
  * The adapter is NEVER live-executable. Missing/ambiguous/unsafe inputs block
    (fail closed).

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path

# Upstream authority layers. This batch CONSUMES their outputs and REUSES their
# scanners + verified documentation facts; it never re-declares risky literals
# and never bypasses the redaction / financial-advice authority.
from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import editorial_preview_supervised_dry_run_contract as editorial
from live_contentops import provider_live_gate_design_contract as design

TASK_LABEL = (
    "TASK_CONTENTOPS_0174TY_TZ_UA_TELEGRAM_LOCAL_ADAPTER_AND_ONE_REQUEST_"
    "BUILDER_BATCH_V0"
)
MODEL = "TELEGRAM_LOCAL_ADAPTER_CONTRACT_0174TY_TZ_UA"
MODEL_VERSION = "0174TY_TZ_UA_TELEGRAM_LOCAL_ADAPTER_V1"

RENDERED_PAYLOAD_SCHEMA = "contentops.telegram_rendered_payload"
RENDERED_PAYLOAD_SCHEMA_VERSION = "0174TY_TELEGRAM_RENDERED_PAYLOAD_V1"
ONE_REQUEST_SCHEMA = "contentops.telegram_one_request_object"
ONE_REQUEST_SCHEMA_VERSION = "0174TZ_TELEGRAM_ONE_REQUEST_OBJECT_V1"
CAPABILITY_ENFORCER_SCHEMA = "contentops.telegram_adapter_capability_enforcer"
CAPABILITY_ENFORCER_SCHEMA_VERSION = "0174TZ_TELEGRAM_CAPABILITY_ENFORCER_V1"
RESPONSE_SHAPE_SCHEMA = "contentops.redacted_telegram_response_shape"
RESPONSE_SHAPE_SCHEMA_VERSION = "0174UA_REDACTED_TELEGRAM_RESPONSE_SHAPE_V1"
ADAPTER_READINESS_SCHEMA = "contentops.telegram_local_adapter_readiness"
ADAPTER_READINESS_SCHEMA_VERSION = "0174UA_TELEGRAM_LOCAL_ADAPTER_READINESS_V1"

SOURCE_BASELINE_COMMIT = "29ddea91e7d7d86ec54d558965da6f0c5f8e8d86"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174TY_TZ_UA")
PACKET_FILENAME = "telegram_local_adapter_contract_packet.json"
DOC_FILENAME = "telegram_local_adapter_contract.md"

NEXT_REQUIRED_GATE = (
    "an operator-owned live gate that hydrates the Telegram bot credential "
    "handle ONCE, runs a single read-only identity check, confirms the "
    "approved payload hash binding, and only then performs EXACTLY one "
    "supervised send; credential hydration, transport, and any live platform "
    "call remain separate future operator-owned gates and are NOT enabled here"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174UB_UC_UD_TELEGRAM_OPERATOR_LIVE_GATE_TRANSPORT_"
    "BOUNDARY_AND_SINGLE_SEND_EXECUTION_HARNESS_DESIGN_BATCH_V0"
)


# --------------------------------------------------------------------------- #
# Status vocabularies (symbolic only) -- reuse upstream PASS/BLOCKED/FAIL_CLOSED
# --------------------------------------------------------------------------- #
class Status:
    PASS = design.Status.PASS
    BLOCKED = design.Status.BLOCKED
    FAIL_CLOSED = design.Status.FAIL_CLOSED


# Provider identity + verified facts are imported from the accepted design
# contract so no risky literal (host, path template, method names) is
# re-declared here.
PROVIDER_TELEGRAM = design.PROVIDER_TELEGRAM
TELEGRAM_API_HOST = design.TELEGRAM_API_HOST
TELEGRAM_METHOD_PATH_TEMPLATE = design.TELEGRAM_METHOD_PATH_TEMPLATE
METHOD_SUPERVISED_SEND = design.METHOD_SUPERVISED_SEND
METHOD_READ_ONLY_IDENTITY = design.METHOD_READ_ONLY_IDENTITY
INBOUND_METHODS_NOT_USED = design.INBOUND_METHODS_NOT_USED
TELEGRAM_MAX_TEXT_LENGTH = design.TELEGRAM_MAX_TEXT_LENGTH
TELEGRAM_MIN_TEXT_LENGTH = design.TELEGRAM_MIN_TEXT_LENGTH
PARSE_MODE_OPTIONS = design.PARSE_MODE_OPTIONS
SUPERVISED_SEND_REQUIRED_PARAMS = design.SUPERVISED_SEND_REQUIRED_PARAMS
SUPERVISED_SEND_OPTIONAL_PARAMS = design.SUPERVISED_SEND_OPTIONAL_PARAMS

# A symbolic "no parse mode" sentinel for plain text.
PARSE_MODE_NONE = "none"
PARSE_MODE_CHOICES = tuple(PARSE_MODE_OPTIONS) + (PARSE_MODE_NONE,)

# The ONLY capability this local adapter recognises for now: the supervised
# one-request text send. Everything else is rejected by the enforcer.
ALLOWED_CAPABILITY = "supervised_one_request_text_send"

# Automation classes that are explicitly rejected for now (recorded as symbolic
# capability NAMES only -- never executed). The provider method names for
# inbound receiving are reused from the design contract's tuple so they live in
# data, not as fresh code literals.
REJECTED_AUTOMATION_CLASSES = (
    "media_send",
    "message_edit",
    "message_delete",
    "reply_automation",
    "inbound_receiving",
)

# Symbolic redacted response status classes (no raw provider response stored).
RESPONSE_STATUS_OK_CLASS = "provider_status_ok_class"
RESPONSE_STATUS_ERROR_CLASS = "provider_status_error_class"
RESPONSE_STATUS_UNKNOWN_CLASS = "provider_status_unknown_class"
RESPONSE_STATUS_CLASSES = (
    RESPONSE_STATUS_OK_CLASS,
    RESPONSE_STATUS_ERROR_CLASS,
    RESPONSE_STATUS_UNKNOWN_CLASS,
)

# Symbolic provider status-code classes (never a raw numeric code chain).
PROVIDER_CODE_SUCCESS_CLASS = "provider_code_success_class"
PROVIDER_CODE_CLIENT_ERROR_CLASS = "provider_code_client_error_class"
PROVIDER_CODE_SERVER_ERROR_CLASS = "provider_code_server_error_class"
PROVIDER_CODE_UNKNOWN_CLASS = "provider_code_unknown_class"
PROVIDER_CODE_CLASSES = (
    PROVIDER_CODE_SUCCESS_CLASS,
    PROVIDER_CODE_CLIENT_ERROR_CLASS,
    PROVIDER_CODE_SERVER_ERROR_CLASS,
    PROVIDER_CODE_UNKNOWN_CLASS,
)

# Symbolic redacted message-id classes (never a raw provider message id).
MESSAGE_ID_PRESENT_CLASS = "redacted_message_id_present_class"
MESSAGE_ID_ABSENT_CLASS = "redacted_message_id_absent_class"
MESSAGE_ID_CLASSES = (MESSAGE_ID_PRESENT_CLASS, MESSAGE_ID_ABSENT_CLASS)

# Outcome classes.
RENDER_OK = "telegram_rendered_payload_ok_not_live"
RENDER_BLOCKED = "telegram_rendered_payload_blocked"
RENDER_FAIL_CLOSED = "telegram_rendered_payload_fail_closed_forbidden_value"

REQUEST_OK = "telegram_one_request_object_built_not_live"
REQUEST_BLOCKED = "telegram_one_request_object_blocked"
REQUEST_FAIL_CLOSED = "telegram_one_request_object_fail_closed_forbidden_value"

ENFORCER_ALLOWED = "telegram_capability_allowed_not_live"
ENFORCER_BLOCKED = "telegram_capability_blocked"
ENFORCER_FAIL_CLOSED = "telegram_capability_fail_closed_forbidden_value"

ADAPTER_READY = "telegram_local_adapter_ready_not_live"
ADAPTER_BLOCKED = "telegram_local_adapter_blocked"
ADAPTER_FAIL_CLOSED = "telegram_local_adapter_fail_closed_forbidden_value"

# Blocked-reason classes.
BLOCK_FORBIDDEN_VALUE = "adapter_forbidden_value_detected"
BLOCK_FINANCIAL_ADVICE = "adapter_financial_advice_detected"
BLOCK_TEXT_EMPTY = "rendered_text_empty"
BLOCK_TEXT_LENGTH_OUT_OF_BOUNDS = "rendered_text_length_out_of_documented_bounds"
BLOCK_PARSE_MODE_NOT_ALLOWLISTED = "parse_mode_not_allowlisted"
BLOCK_CAPABILITY_NOT_ALLOWED = "capability_not_the_text_one_request_path"
BLOCK_AUTOMATION_REJECTED = "automation_class_rejected"
BLOCK_INBOUND_RECEIVING_USED = "inbound_receiving_method_used"
BLOCK_METHOD_NOT_SUPERVISED_SEND = "method_is_not_supervised_send"
BLOCK_OPTIONAL_PARAM_NOT_ALLOWLISTED = "optional_param_not_allowlisted"
BLOCK_CREDENTIAL_HANDLE_MISSING = "credential_handle_id_missing"
BLOCK_DESTINATION_BINDING_MISSING = "destination_binding_id_missing"
BLOCK_RENDERED_PAYLOAD_NOT_OK = "rendered_payload_not_ok"
BLOCK_REQUEST_OBJECT_NOT_BUILT = "one_request_object_not_built"
BLOCK_CAPABILITY_NOT_ENFORCED = "capability_enforcer_not_allowed"
BLOCK_DESIGN_NOT_RECORDED = "provider_live_gate_design_not_recorded"

# R1-style upstream unsafe-behavior revalidation reasons.
BLOCK_DESIGN_UNSAFE_BEHAVIOR = "adapter_design_unsafe_behavior_claimed"
BLOCK_RENDERED_UNSAFE_BEHAVIOR = "adapter_rendered_unsafe_behavior_claimed"
BLOCK_REQUEST_UNSAFE_BEHAVIOR = "adapter_request_unsafe_behavior_claimed"
BLOCK_ENFORCER_UNSAFE_BEHAVIOR = "adapter_enforcer_unsafe_behavior_claimed"

# Artifact-name labels passed to detect_unsafe_behavior_claims.
ARTIFACT_DESIGN = "design"
ARTIFACT_RENDERED = "rendered"
ARTIFACT_REQUEST = "request"
ARTIFACT_ENFORCER = "enforcer"

_ARTIFACT_UNSAFE_BASE = {
    ARTIFACT_DESIGN: BLOCK_DESIGN_UNSAFE_BEHAVIOR,
    ARTIFACT_RENDERED: BLOCK_RENDERED_UNSAFE_BEHAVIOR,
    ARTIFACT_REQUEST: BLOCK_REQUEST_UNSAFE_BEHAVIOR,
    ARTIFACT_ENFORCER: BLOCK_ENFORCER_UNSAFE_BEHAVIOR,
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

# Adapter-specific readiness booleans that MUST be False where present.
_UNSAFE_READINESS_FLAGS = (
    "adapter_is_dispatch",
    "adapter_is_live_readiness",
    "adapter_is_credential_hydration",
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
    """Hard-coded safety invariants attached to every 0174TY/TZ/UA object."""
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

    A consumed upstream artifact (the provider live-gate design, a rendered
    payload, a one-request object, or a capability enforcer result) must NOT be
    able to carry a tampered flag claiming live/network/credential/scheduler/
    retry/dispatch behavior past this adapter just because its status metadata
    still reads clear. This helper re-derives the truth directly from the flags.

    A universal flag "claims" unsafe behavior when it is present and not False.
    An adapter-specific readiness boolean likewise blocks when present and not
    False. Returns a sorted, de-duplicated list whose first element (when any
    flag trips) is the artifact's bare unsafe-behavior-claimed class, followed
    by ``<base>:<flag>`` entries. An empty list means no unsafe behavior.
    """
    o = obj or {}
    base = _ARTIFACT_UNSAFE_BASE.get(
        artifact_name,
        "adapter_" + str(artifact_name) + "_unsafe_behavior_claimed")
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
# 0174TY: TelegramRenderedPayload
# --------------------------------------------------------------------------- #
def render_telegram_payload(*, approved_text, preview_text=None,
                            parse_mode=PARSE_MODE_NONE,
                            content_lane=None):
    """Render an approved/safe text artifact into a TelegramRenderedPayload.

    Fail-closed. Keeps the preview text and the send text separated. Blocks:

      * forbidden raw credential/chat/webhook/token-like material => fail_closed;
      * financial-advice / signal framing => fail_closed;
      * empty send text;
      * send text outside the documented [1, 4096] bound;
      * a parse mode not on the symbolic allow-list (HTML/MarkdownV2/Markdown/
        none).

    The returned value records only the SEND text length and a content
    checksum; it does not expose raw secret material (the scanner guarantees the
    approved text itself is non-secret editorial content).
    """
    send_text = approved_text if approved_text is not None else ""
    preview = preview_text if preview_text is not None else send_text

    scan_payload = {
        "approved_text": send_text,
        "preview_text": preview,
        "parse_mode": parse_mode,
        "content_lane": content_lane,
    }
    if scan_for_leaks(scan_payload):
        return _render_result(
            RENDER_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE], ok=False,
            forbidden_detected=True, financial_detected=False,
            send_text=send_text, preview_text=preview, parse_mode=parse_mode,
            content_lane=content_lane)

    if scan_for_financial_advice(scan_payload):
        return _render_result(
            RENDER_FAIL_CLOSED, blocked=[BLOCK_FINANCIAL_ADVICE], ok=False,
            forbidden_detected=False, financial_detected=True,
            send_text=send_text, preview_text=preview, parse_mode=parse_mode,
            content_lane=content_lane)

    blocked = []
    text_len = len(send_text)
    if text_len < TELEGRAM_MIN_TEXT_LENGTH:
        blocked.append(BLOCK_TEXT_EMPTY)
    elif text_len > TELEGRAM_MAX_TEXT_LENGTH:
        blocked.append(BLOCK_TEXT_LENGTH_OUT_OF_BOUNDS)

    if parse_mode not in PARSE_MODE_CHOICES:
        blocked.append(BLOCK_PARSE_MODE_NOT_ALLOWLISTED)

    ok = not blocked
    outcome = RENDER_OK if ok else RENDER_BLOCKED
    return _render_result(
        outcome, blocked=sorted(set(blocked)), ok=ok, forbidden_detected=False,
        financial_detected=False, send_text=send_text, preview_text=preview,
        parse_mode=parse_mode, content_lane=content_lane)


def _render_result(outcome_class, *, blocked, ok, forbidden_detected,
                   financial_detected, send_text, preview_text, parse_mode,
                   content_lane):
    """Build a deterministic TelegramRenderedPayload (pure value)."""
    if forbidden_detected or financial_detected:
        status = Status.FAIL_CLOSED
    elif ok:
        status = Status.PASS
    else:
        status = Status.BLOCKED
    # Only lengths + a content checksum are persisted for the texts; the raw
    # send/preview text is echoed back ONLY when render is OK and scanner-clean
    # (editorial content, not secret material), so callers can build a request.
    expose_text = ok and not (forbidden_detected or financial_detected)
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "rendered_payload_schema": RENDERED_PAYLOAD_SCHEMA,
        "rendered_payload_schema_version": RENDERED_PAYLOAD_SCHEMA_VERSION,
        "status": status,
        "rendered_payload_outcome_class": outcome_class,
        "rendered_payload_ok": ok,
        "provider": PROVIDER_TELEGRAM,
        "send_text": send_text if expose_text else None,
        "preview_text": preview_text if expose_text else None,
        "send_text_length": len(send_text),
        "preview_text_length": len(preview_text),
        "preview_and_send_separated": True,
        "parse_mode": parse_mode,
        "parse_mode_allowlist": list(PARSE_MODE_CHOICES),
        "content_lane": content_lane,
        "min_text_length": TELEGRAM_MIN_TEXT_LENGTH,
        "max_text_length": TELEGRAM_MAX_TEXT_LENGTH,
        "send_text_checksum": hashlib.sha256(
            send_text.encode("utf-8")).hexdigest(),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_detected,
        # Hard invariants -- a rendered payload is NEVER dispatch / live.
        **_safety_flags(),
        "adapter_is_dispatch": False,
        "adapter_is_live_readiness": False,
    }
    result["rendered_payload_checksum"] = compute_checksum(result)
    return result


def _rendered_is_ok(rendered):
    r = rendered or {}
    return (
        r.get("rendered_payload_outcome_class") == RENDER_OK
        and r.get("rendered_payload_ok") is True
        and r.get("status") == Status.PASS
    )


# --------------------------------------------------------------------------- #
# 0174TZ: TelegramAdapterCapabilityEnforcer
# --------------------------------------------------------------------------- #
def enforce_capability(*, requested_capability=ALLOWED_CAPABILITY,
                       requested_method=METHOD_SUPERVISED_SEND,
                       requested_optional_params=(),
                       requested_automation_classes=()):
    """Allow ONLY the supervised one-request text-send path. Fail-closed.

    Blocks:

      * forbidden material => fail_closed;
      * a capability other than the text one-request path;
      * a method other than the supervised send;
      * any inbound-receiving method (getUpdates/setWebhook-class);
      * any media/edit/delete/reply automation class;
      * any optional param not on the documented allow-list.
    """
    optional_params = [str(p) for p in (requested_optional_params or ())]
    automation = [str(a) for a in (requested_automation_classes or ())]

    scan_payload = {
        "requested_capability": requested_capability,
        "requested_method": requested_method,
        "requested_optional_params": optional_params,
        "requested_automation_classes": automation,
    }
    if scan_for_leaks(scan_payload):
        return _enforcer_result(
            ENFORCER_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE],
            allowed=False, forbidden_detected=True,
            requested_capability=requested_capability,
            requested_method=requested_method, optional_params=optional_params,
            automation=automation)

    blocked = []
    if requested_capability != ALLOWED_CAPABILITY:
        blocked.append(BLOCK_CAPABILITY_NOT_ALLOWED)

    if requested_method != METHOD_SUPERVISED_SEND:
        blocked.append(BLOCK_METHOD_NOT_SUPERVISED_SEND)
    if requested_method in INBOUND_METHODS_NOT_USED:
        blocked.append(BLOCK_INBOUND_RECEIVING_USED)

    for a in automation:
        if a == "inbound_receiving":
            blocked.append(BLOCK_INBOUND_RECEIVING_USED)
        if a in REJECTED_AUTOMATION_CLASSES:
            blocked.append(BLOCK_AUTOMATION_REJECTED + ":" + a)

    for p in optional_params:
        if p in INBOUND_METHODS_NOT_USED:
            blocked.append(BLOCK_INBOUND_RECEIVING_USED)
        if p not in SUPERVISED_SEND_OPTIONAL_PARAMS:
            blocked.append(BLOCK_OPTIONAL_PARAM_NOT_ALLOWLISTED + ":" + p)

    allowed = not blocked
    outcome = ENFORCER_ALLOWED if allowed else ENFORCER_BLOCKED
    return _enforcer_result(
        outcome, blocked=sorted(set(blocked)), allowed=allowed,
        forbidden_detected=False, requested_capability=requested_capability,
        requested_method=requested_method, optional_params=optional_params,
        automation=automation)


def _enforcer_result(outcome_class, *, blocked, allowed, forbidden_detected,
                     requested_capability, requested_method, optional_params,
                     automation):
    """Build a deterministic TelegramAdapterCapabilityEnforcer (pure value)."""
    status = (Status.PASS if allowed
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "capability_enforcer_schema": CAPABILITY_ENFORCER_SCHEMA,
        "capability_enforcer_schema_version": CAPABILITY_ENFORCER_SCHEMA_VERSION,
        "status": status,
        "capability_enforcer_outcome_class": outcome_class,
        "capability_allowed": allowed,
        "allowed_capability": ALLOWED_CAPABILITY,
        "requested_capability": requested_capability,
        "requested_method": requested_method,
        "supervised_send_method": METHOD_SUPERVISED_SEND,
        "optional_param_allowlist": list(SUPERVISED_SEND_OPTIONAL_PARAMS),
        "requested_optional_param_names": sorted(set(optional_params)),
        "rejected_automation_classes": list(REJECTED_AUTOMATION_CLASSES),
        "requested_automation_classes": sorted(set(automation)),
        "inbound_methods_not_used": list(INBOUND_METHODS_NOT_USED),
        "inbound_receiving_used": False,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- the enforcer is NEVER dispatch / live.
        **_safety_flags(),
        "adapter_is_dispatch": False,
        "adapter_is_live_readiness": False,
    }
    result["capability_enforcer_checksum"] = compute_checksum(result)
    return result


def _enforcer_is_allowed(enforcer):
    e = enforcer or {}
    return (
        e.get("capability_enforcer_outcome_class") == ENFORCER_ALLOWED
        and e.get("capability_allowed") is True
        and e.get("status") == Status.PASS
    )


# --------------------------------------------------------------------------- #
# 0174TZ: TelegramOneRequestObject
# --------------------------------------------------------------------------- #
def build_one_request_object(rendered_payload, capability_enforcer, *,
                             credential_handle_id, destination_binding_id,
                             optional_params=(), request_id=None):
    """Build a deterministic request object for a FUTURE supervised send.

    Fail-closed. The object NEVER contains a URL with a token, a token value, or
    a raw chat id: the credential and destination are referenced ONLY by
    symbolic ids and the credentialed path uses the symbolic template. The
    method is recorded as a symbolic method string. ``request_count_authorized``
    is exactly 1, with no auto retry / scheduler / webhook / polling.

    Blocks when:

      * forbidden material => fail_closed;
      * the rendered payload is not OK;
      * the capability enforcer did not allow the path;
      * a credential handle / destination binding id is missing;
      * the rendered payload or enforcer claims unsafe behavior (R1).
    """
    rp = rendered_payload or {}
    en = capability_enforcer or {}
    opt = [str(p) for p in (optional_params or ())]

    scan_payload = {
        "credential_handle_id": credential_handle_id,
        "destination_binding_id": destination_binding_id,
        "optional_params": opt,
        "request_id": request_id,
    }
    if scan_for_leaks([rp, en, scan_payload]):
        return _request_result(
            REQUEST_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE], built=False,
            forbidden_detected=True, rendered_payload=rp,
            capability_enforcer=en, credential_handle_id=credential_handle_id,
            destination_binding_id=destination_binding_id, optional_params=opt,
            request_id=request_id)

    blocked = []
    if not _rendered_is_ok(rp):
        blocked.append(BLOCK_RENDERED_PAYLOAD_NOT_OK)
    if not _enforcer_is_allowed(en):
        blocked.append(BLOCK_CAPABILITY_NOT_ENFORCED)
    if not credential_handle_id:
        blocked.append(BLOCK_CREDENTIAL_HANDLE_MISSING)
    if not destination_binding_id:
        blocked.append(BLOCK_DESTINATION_BINDING_MISSING)

    for p in opt:
        if p not in SUPERVISED_SEND_OPTIONAL_PARAMS:
            blocked.append(BLOCK_OPTIONAL_PARAM_NOT_ALLOWLISTED + ":" + p)

    # R1 upstream safety-flag revalidation across consumed artifacts.
    blocked.extend(detect_unsafe_behavior_claims(rp, ARTIFACT_RENDERED))
    blocked.extend(detect_unsafe_behavior_claims(en, ARTIFACT_ENFORCER))

    built = not blocked
    outcome = REQUEST_OK if built else REQUEST_BLOCKED
    return _request_result(
        outcome, blocked=sorted(set(blocked)), built=built,
        forbidden_detected=False, rendered_payload=rp, capability_enforcer=en,
        credential_handle_id=credential_handle_id,
        destination_binding_id=destination_binding_id, optional_params=opt,
        request_id=request_id)


def _request_result(outcome_class, *, blocked, built, forbidden_detected,
                    rendered_payload, capability_enforcer, credential_handle_id,
                    destination_binding_id, optional_params, request_id):
    """Build a deterministic TelegramOneRequestObject (pure value)."""
    status = (Status.PASS if built
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    rp = rendered_payload or {}

    # The future-request descriptor. It references the credential ONLY by handle
    # and the destination ONLY by binding; the path is the symbolic template; no
    # URL, token, or raw chat id is ever present.
    request_descriptor = {
        "provider": PROVIDER_TELEGRAM,
        "api_host": TELEGRAM_API_HOST,
        "method_name": METHOD_SUPERVISED_SEND,
        "method_path_template": TELEGRAM_METHOD_PATH_TEMPLATE,
        "credential_handle_id": credential_handle_id,
        "destination_binding_id": destination_binding_id,
        "credential_referenced_by_handle_only": True,
        "destination_referenced_by_binding_only": True,
        "contains_url_with_token": False,
        "contains_token_value": False,
        "contains_raw_chat_id": False,
        "send_text_checksum": rp.get("send_text_checksum"),
        "parse_mode": rp.get("parse_mode"),
        "optional_param_names": sorted(set(optional_params)),
        "request_count_authorized": 1,
        "auto_retry_allowed": False,
        "scheduler_enabled": False,
        "webhook_registered": False,
        "polling_enabled": False,
    }
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "one_request_schema": ONE_REQUEST_SCHEMA,
        "one_request_schema_version": ONE_REQUEST_SCHEMA_VERSION,
        "status": status,
        "one_request_outcome_class": outcome_class,
        "one_request_built": built,
        "request_id": request_id,
        "provider": PROVIDER_TELEGRAM,
        "request_descriptor": request_descriptor,
        "request_count_authorized": 1,
        "credential_handle_id": credential_handle_id,
        "destination_binding_id": destination_binding_id,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- the request object is NEVER dispatch / live.
        **_safety_flags(),
        "adapter_is_dispatch": False,
        "adapter_is_live_readiness": False,
        "adapter_is_credential_hydration": False,
        "valid_for_live_execution": False,
        "no_raw_credential_stored": True,
    }
    result["one_request_checksum"] = compute_checksum(result)
    return result


def _request_is_built(request_object):
    r = request_object or {}
    return (
        r.get("one_request_outcome_class") == REQUEST_OK
        and r.get("one_request_built") is True
        and r.get("status") == Status.PASS
        and r.get("request_count_authorized") == 1
    )


# --------------------------------------------------------------------------- #
# 0174UA: RedactedTelegramResponseShape (FUTURE-ONLY)
# --------------------------------------------------------------------------- #
def build_redacted_response_shape(*, response_status_class=RESPONSE_STATUS_UNKNOWN_CLASS,
                                  provider_code_class=PROVIDER_CODE_UNKNOWN_CLASS,
                                  message_id_class=MESSAGE_ID_ABSENT_CLASS,
                                  request_checksum=None,
                                  response_checksum=None):
    """Build a FUTURE-ONLY redacted provider-response shape. Fail-closed.

    Stores ONLY the symbolic redacted status class, the symbolic provider
    status-code class, the symbolic redacted message-id class, and the request
    / response checksums. It NEVER stores a raw provider response, raw chat id,
    raw token, raw URL, headers, or cookies. Unknown symbolic classes are
    coerced to the explicit unknown/absent class (never persisted raw).
    """
    blocked = []
    scan_payload = {
        "response_status_class": response_status_class,
        "provider_code_class": provider_code_class,
        "message_id_class": message_id_class,
        "request_checksum": request_checksum,
        "response_checksum": response_checksum,
    }
    forbidden_detected = bool(scan_for_leaks(scan_payload))
    if forbidden_detected:
        blocked.append(BLOCK_FORBIDDEN_VALUE)

    status_class = (response_status_class
                    if response_status_class in RESPONSE_STATUS_CLASSES
                    else RESPONSE_STATUS_UNKNOWN_CLASS)
    code_class = (provider_code_class
                  if provider_code_class in PROVIDER_CODE_CLASSES
                  else PROVIDER_CODE_UNKNOWN_CLASS)
    msg_class = (message_id_class
                 if message_id_class in MESSAGE_ID_CLASSES
                 else MESSAGE_ID_ABSENT_CLASS)

    status = Status.FAIL_CLOSED if forbidden_detected else Status.PASS
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "response_shape_schema": RESPONSE_SHAPE_SCHEMA,
        "response_shape_schema_version": RESPONSE_SHAPE_SCHEMA_VERSION,
        "status": status,
        "provider": PROVIDER_TELEGRAM,
        "is_future_only_shape": True,
        "response_status_class": status_class,
        "provider_code_class": code_class,
        "redacted_message_id_class": msg_class,
        "request_checksum": request_checksum,
        "response_checksum": response_checksum,
        "response_status_classes": list(RESPONSE_STATUS_CLASSES),
        "provider_code_classes": list(PROVIDER_CODE_CLASSES),
        "message_id_classes": list(MESSAGE_ID_CLASSES),
        # Explicit "stores no raw X" invariants.
        "stores_raw_provider_response": False,
        "stores_raw_chat_id": False,
        "stores_raw_token": False,
        "stores_raw_url": False,
        "stores_headers": False,
        "stores_cookies": False,
        "blocked_reasons": sorted(set(blocked)),
        "forbidden_fields_detected": forbidden_detected,
        **_safety_flags(),
        "adapter_is_dispatch": False,
        "adapter_is_live_readiness": False,
    }
    result["response_shape_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# 0174UA: Local adapter readiness classifier
# --------------------------------------------------------------------------- #
def classify_local_adapter_readiness(rendered_payload, capability_enforcer,
                                     one_request_object, *,
                                     provider_live_gate_design=None,
                                     response_shape=None):
    """Classify the LOCAL adapter readiness. Fail-closed. NEVER live.

    Returns ``telegram_local_adapter_ready_not_live`` only when ALL hold:

      * no forbidden material and no financial advice in any consumed artifact;
      * the rendered payload is OK;
      * the capability enforcer allowed the text one-request path;
      * the one-request object was built with exactly one authorized request;
      * if a provider live-gate design is supplied, it is recorded;
      * no consumed artifact claims unsafe behavior (R1 revalidation).

    The result is NEVER ``live_ready`` and NEVER ``valid_for_live_execution``;
    it always ``requires_operator_live_gate``.
    """
    rp = rendered_payload or {}
    en = capability_enforcer or {}
    ro = one_request_object or {}
    dz = provider_live_gate_design or {}
    rs = response_shape or {}
    blocked = []

    consumed = [rp, en, ro, dz, rs]
    if scan_for_leaks(consumed):
        return _readiness_result(
            ADAPTER_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE], ready=False,
            forbidden_detected=True, financial_detected=False,
            rendered_payload=rp, capability_enforcer=en,
            one_request_object=ro, provider_live_gate_design=dz,
            response_shape=rs)

    if scan_for_financial_advice(consumed):
        return _readiness_result(
            ADAPTER_FAIL_CLOSED, blocked=[BLOCK_FINANCIAL_ADVICE], ready=False,
            forbidden_detected=False, financial_detected=True,
            rendered_payload=rp, capability_enforcer=en,
            one_request_object=ro, provider_live_gate_design=dz,
            response_shape=rs)

    if not _rendered_is_ok(rp):
        blocked.append(BLOCK_RENDERED_PAYLOAD_NOT_OK)
    if not _enforcer_is_allowed(en):
        blocked.append(BLOCK_CAPABILITY_NOT_ENFORCED)
    if not _request_is_built(ro):
        blocked.append(BLOCK_REQUEST_OBJECT_NOT_BUILT)

    if provider_live_gate_design is not None:
        if dz.get("provider_live_gate_design_outcome_class") != (
                design.DESIGN_RECORDED):
            blocked.append(BLOCK_DESIGN_NOT_RECORDED)
        blocked.extend(detect_unsafe_behavior_claims(dz, ARTIFACT_DESIGN))

    # R1 upstream safety-flag revalidation across consumed artifacts.
    blocked.extend(detect_unsafe_behavior_claims(rp, ARTIFACT_RENDERED))
    blocked.extend(detect_unsafe_behavior_claims(en, ARTIFACT_ENFORCER))
    blocked.extend(detect_unsafe_behavior_claims(ro, ARTIFACT_REQUEST))

    ready = not blocked
    outcome = ADAPTER_READY if ready else ADAPTER_BLOCKED
    return _readiness_result(
        outcome, blocked=sorted(set(blocked)), ready=ready,
        forbidden_detected=False, financial_detected=False,
        rendered_payload=rp, capability_enforcer=en, one_request_object=ro,
        provider_live_gate_design=dz, response_shape=rs)


def _readiness_result(outcome_class, *, blocked, ready, forbidden_detected,
                      financial_detected, rendered_payload, capability_enforcer,
                      one_request_object, provider_live_gate_design,
                      response_shape):
    """Build a deterministic local-adapter readiness classification."""
    if forbidden_detected or financial_detected:
        status = Status.FAIL_CLOSED
    elif ready:
        status = Status.PASS
    else:
        status = Status.BLOCKED
    ro = one_request_object or {}
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "adapter_readiness_schema": ADAPTER_READINESS_SCHEMA,
        "adapter_readiness_schema_version": ADAPTER_READINESS_SCHEMA_VERSION,
        "status": status,
        "adapter_readiness_outcome_class": outcome_class,
        "telegram_local_adapter_ready_not_live": ready,
        "provider": PROVIDER_TELEGRAM,
        "request_count_authorized": ro.get("request_count_authorized")
        if ro else None,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_detected,
        "requires_operator_live_gate": True,
        # Hard invariants -- the adapter is NEVER live.
        **_safety_flags(),
        "adapter_is_dispatch": False,
        "adapter_is_live_readiness": False,
        "adapter_is_credential_hydration": False,
        "valid_for_live_execution": False,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    result["adapter_readiness_checksum"] = compute_checksum(result)
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
        "rendered_payload_schema": RENDERED_PAYLOAD_SCHEMA,
        "rendered_payload_schema_version": RENDERED_PAYLOAD_SCHEMA_VERSION,
        "one_request_schema": ONE_REQUEST_SCHEMA,
        "one_request_schema_version": ONE_REQUEST_SCHEMA_VERSION,
        "capability_enforcer_schema": CAPABILITY_ENFORCER_SCHEMA,
        "capability_enforcer_schema_version": CAPABILITY_ENFORCER_SCHEMA_VERSION,
        "response_shape_schema": RESPONSE_SHAPE_SCHEMA,
        "response_shape_schema_version": RESPONSE_SHAPE_SCHEMA_VERSION,
        "adapter_readiness_schema": ADAPTER_READINESS_SCHEMA,
        "adapter_readiness_schema_version": ADAPTER_READINESS_SCHEMA_VERSION,
        "provider": PROVIDER_TELEGRAM,
        "api_host": TELEGRAM_API_HOST,
        "method_path_template": TELEGRAM_METHOD_PATH_TEMPLATE,
        "supervised_send_method": METHOD_SUPERVISED_SEND,
        "read_only_identity_method": METHOD_READ_ONLY_IDENTITY,
        "inbound_methods_not_used": list(INBOUND_METHODS_NOT_USED),
        "allowed_capability": ALLOWED_CAPABILITY,
        "rejected_automation_classes": list(REJECTED_AUTOMATION_CLASSES),
        "required_param_names": list(SUPERVISED_SEND_REQUIRED_PARAMS),
        "optional_param_allowlist": list(SUPERVISED_SEND_OPTIONAL_PARAMS),
        "parse_mode_allowlist": list(PARSE_MODE_CHOICES),
        "min_text_length": TELEGRAM_MIN_TEXT_LENGTH,
        "max_text_length": TELEGRAM_MAX_TEXT_LENGTH,
        "response_status_classes": list(RESPONSE_STATUS_CLASSES),
        "provider_code_classes": list(PROVIDER_CODE_CLASSES),
        "message_id_classes": list(MESSAGE_ID_CLASSES),
        "rendered_payload_outcome_classes": [
            RENDER_OK, RENDER_BLOCKED, RENDER_FAIL_CLOSED,
        ],
        "one_request_outcome_classes": [
            REQUEST_OK, REQUEST_BLOCKED, REQUEST_FAIL_CLOSED,
        ],
        "capability_enforcer_outcome_classes": [
            ENFORCER_ALLOWED, ENFORCER_BLOCKED, ENFORCER_FAIL_CLOSED,
        ],
        "adapter_readiness_outcome_classes": [
            ADAPTER_READY, ADAPTER_BLOCKED, ADAPTER_FAIL_CLOSED,
        ],
        "r1_upstream_revalidation_blocked_reasons": [
            BLOCK_DESIGN_UNSAFE_BEHAVIOR,
            BLOCK_RENDERED_UNSAFE_BEHAVIOR,
            BLOCK_REQUEST_UNSAFE_BEHAVIOR,
            BLOCK_ENFORCER_UNSAFE_BEHAVIOR,
        ],
        "r1_revalidated_unsafe_flags": list(
            _UNSAFE_BEHAVIOR_FLAGS + _UNSAFE_READINESS_FLAGS),
        "hard_invariants": [
            "real_core_adapter_code_but_never_live",
            "supervised_post_maps_to_exactly_one_send_method",
            "request_object_has_exactly_one_future_request",
            "request_object_has_no_url_with_token",
            "request_object_has_no_token_value",
            "request_object_has_no_raw_chat_id",
            "credential_referenced_by_handle_only",
            "destination_referenced_by_binding_only",
            "only_text_one_request_path_allowed",
            "inbound_receiving_rejected",
            "media_edit_delete_reply_automation_rejected",
            "non_allowlisted_optional_param_rejected",
            "preview_and_send_text_separated",
            "response_shape_is_future_only",
            "response_shape_stores_no_raw_provider_response",
            "response_shape_stores_no_headers_or_cookies",
            "adapter_is_not_dispatch",
            "adapter_is_not_live_readiness",
            "adapter_is_not_credential_hydration",
            "adapter_requires_operator_owned_live_gate",
            "unsafe_upstream_behavior_claim_blocks_adapter",
            "no_credential_hydration",
            "no_platform_api",
            "no_telegram_send",
            "no_network",
            "no_scheduler",
            "no_retries",
            "no_webhook_or_polling",
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
    rejected = "\n".join(
        f"  * `{c}`" for c in packet["rejected_automation_classes"])
    hard = "\n".join(f"  * `{inv}`" for inv in packet["hard_invariants"])
    r1_reasons = "\n".join(
        f"  * `{r}`"
        for r in packet["r1_upstream_revalidation_blocked_reasons"])
    response_classes = "\n".join(
        f"  * `{c}`" for c in (
            packet["response_status_classes"]
            + packet["provider_code_classes"]
            + packet["message_id_classes"]))
    return (
        f"# 0174TY/TZ/UA Telegram Local Adapter + One-Request Builder\n\n"
        f"Task: `{TASK_LABEL}`\n\n"
        f"Model: `{MODEL}` version `{MODEL_VERSION}`\n\n"
        f"Baseline commit: `{SOURCE_BASELINE_COMMIT}`\n\n"
        f"## Role\n\n"
        f"This batch is LOCAL, deterministic, and REAL CORE PLATFORM CODE that "
        f"is NEVER LIVE. It performs NO network call, NO live platform API "
        f"call, NO supervised send, NO LLM/provider call, NO env/credential "
        f"read, NO credential hydration, NO scheduler, NO retry loop, and NO "
        f"webhook/polling. It NEVER dispatches.\n\n"
        f"## 0174TY TelegramRenderedPayload\n\n"
        f"Consumes an approved/safe text artifact, validates the documented "
        f"text length bound `[{packet['min_text_length']}, "
        f"{packet['max_text_length']}]`, supports a symbolic parse mode "
        f"({parse_modes}), keeps the preview text and send text separated, and "
        f"fails closed on financial-advice/signal framing and on raw "
        f"credential/chat/webhook/token-like material.\n\n"
        f"Documented required parameters:\n\n{required}\n\n"
        f"Optional-parameter allow-list:\n\n{optional}\n\n"
        f"## 0174TZ One-request object + capability enforcer\n\n"
        f"The one-request object is a deterministic descriptor for a FUTURE "
        f"`{METHOD_SUPERVISED_SEND}`: it has NO URL with a token, NO token "
        f"value, and NO raw chat id; the credential and destination are "
        f"referenced ONLY by symbolic ids; the method is a symbolic method "
        f"string; `request_count_authorized` is exactly 1; and no auto retry / "
        f"scheduler / webhook / polling is present. The capability enforcer "
        f"allows ONLY the `{ALLOWED_CAPABILITY}` path and rejects these "
        f"automation classes:\n\n{rejected}\n\n"
        f"## 0174UA Redacted response shape + readiness classifier\n\n"
        f"The redacted response shape is FUTURE-ONLY and stores only symbolic "
        f"classes plus request/response checksums:\n\n{response_classes}\n\n"
        f"It NEVER stores a raw provider response, raw chat id, raw token, raw "
        f"URL, headers, or cookies. The readiness classifier returns "
        f"`{ADAPTER_READY}` / `{ADAPTER_BLOCKED}` / `{ADAPTER_FAIL_CLOSED}` "
        f"and is NEVER `live_ready` and NEVER `valid_for_live_execution`.\n\n"
        f"## R1 upstream safety-flag revalidation\n\n"
        f"The adapter re-derives upstream safety truth directly from the flags "
        f"on every consumed artifact (provider live-gate design, rendered "
        f"payload, capability enforcer, one-request object). A `pass` status "
        f"can NOT hide a tampered claim of network/platform/Telegram/credential/"
        f"LLM/scheduler/retry/dispatch or live-readiness behavior; any such "
        f"claim blocks:\n\n{r1_reasons}\n\n"
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
