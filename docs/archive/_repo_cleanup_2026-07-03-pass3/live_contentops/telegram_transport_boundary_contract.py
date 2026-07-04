"""Telegram transport-boundary + single-send execution harness DESIGN (NOT LIVE).

Tasks 0174UB (operator-owned credential boundary gate), 0174UC (read-only
identity check design + single-send execution harness design), and 0174UD
(post-request audit design + transport-harness readiness classifier) -- one
deterministic, LOCAL design batch on top of the accepted Telegram core chain:

  * 0174TV/TW/TX: provider documentation review + Telegram capability map +
    one-request architecture design (``ProviderLiveGateDesign``).
  * 0174TY/TZ/UA: Telegram local adapter -- rendered payload, capability
    enforcer, ``TelegramOneRequestObject``, redacted response shape, and the
    local adapter readiness classifier.

Product role of this batch (all LOCAL, all deterministic, REAL CORE DESIGN but
NEVER LIVE -- it is the transport-boundary layer that sits between the built
one-request object and a FUTURE operator-owned live gate):
  1. 0174UB ``TelegramCredentialBoundaryGate`` declares -- symbolically only --
     the FUTURE credential-handle hydration step. It requires an explicit
     operator gate id and a credential handle id, and it NEVER reads env / .env
     / keyring / a credential file / a browser session, and NEVER stores a
     token, bot token, header, cookie, URL-with-token, raw chat id, username, or
     webhook URL. It stays ``credential_boundary_declared_not_hydrated``.
  2. 0174UC ``TelegramReadOnlyIdentityCheckDesign`` is a FUTURE-ONLY design for a
     read-only identity proof using the symbolic ``getMe`` method. It runs NO
     request and performs NO network. It defines the expected REDACTED identity
     proof shape (``identity_check_not_run``,
     ``identity_check_future_operator_gate_required``,
     ``bot_identity_redacted_class``, ``provider_status_code_class``,
     ``response_checksum``) and stores NO provider response.
     ``TelegramSingleSendExecutionHarnessDesign`` is a FUTURE-ONLY single-send
     harness design that consumes a built ``TelegramOneRequestObject`` and states
     the EXACT future execution order: hydrate credential handle once -> run the
     read-only identity check once -> confirm the approved payload-hash binding
     -> execute EXACTLY one send -> record the redacted response shape -> append
     the immutable post-request audit. It executes NOTHING and enables NO auto
     retry / scheduler / polling / webhook / reply automation.
  3. 0174UD ``PostRequestAuditDesign`` is a FUTURE-ONLY audit shape storing only
     symbolic request/response checksums, a provider status class, a redacted
     message-id class, the operator gate id, and a timestamp placeholder class;
     it stores NO raw response/header/cookie/token/chat id/url. The transport-
     harness readiness classifier returns
     ``telegram_transport_harness_design_ready_not_live`` / ``..._blocked`` /
     ``..._fail_closed_forbidden_value`` and is NEVER ``live_ready`` and NEVER
     ``valid_for_live_execution``.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no urllib request
    clients, no socket/ssl/http server, no selenium/playwright, no
    dotenv/keyring/sqlite, no openai/anthropic/telegram/tweepy SDKs.
  * NO network call. NO env / .env / keyring / browser-session / credential
    read. NO OAuth, token exchange/refresh, credential hydration.
  * NO live posting, supervised-send call, identity-check call, platform API
    call, dispatch, scheduler, retry loop, autonomous replies/DMs, scraping, or
    runtime.
  * Raw chat id / username / phone / token / bot token / webhook url / raw
    provider response / profile url / header / cookie are rejected or redacted
    by a fail-closed scanner and never persisted. Provider method/parameter
    NAMES are symbolic documentation vocabulary, never secret material.
  * NO financial advice / signal framing in any design text fails closed.
  * The harness is NEVER live-executable. Missing/ambiguous/unsafe inputs block
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
from live_contentops import telegram_local_adapter_contract as adapter
from live_contentops import provider_live_gate_design_contract as design

TASK_LABEL = (
    "TASK_CONTENTOPS_0174UB_UC_UD_TELEGRAM_OPERATOR_LIVE_GATE_TRANSPORT_"
    "BOUNDARY_AND_SINGLE_SEND_EXECUTION_HARNESS_DESIGN_BATCH_V0"
)
MODEL = "TELEGRAM_TRANSPORT_BOUNDARY_CONTRACT_0174UB_UC_UD"
MODEL_VERSION = "0174UB_UC_UD_TELEGRAM_TRANSPORT_BOUNDARY_V1"

CREDENTIAL_BOUNDARY_SCHEMA = "contentops.telegram_credential_boundary_gate"
CREDENTIAL_BOUNDARY_SCHEMA_VERSION = "0174UB_TELEGRAM_CREDENTIAL_BOUNDARY_GATE_V1"
IDENTITY_CHECK_SCHEMA = "contentops.telegram_read_only_identity_check_design"
IDENTITY_CHECK_SCHEMA_VERSION = "0174UC_TELEGRAM_READ_ONLY_IDENTITY_CHECK_V1"
HARNESS_SCHEMA = "contentops.telegram_single_send_execution_harness_design"
HARNESS_SCHEMA_VERSION = "0174UC_TELEGRAM_SINGLE_SEND_HARNESS_DESIGN_V1"
AUDIT_SCHEMA = "contentops.telegram_post_request_audit_design"
AUDIT_SCHEMA_VERSION = "0174UD_TELEGRAM_POST_REQUEST_AUDIT_DESIGN_V1"
READINESS_SCHEMA = "contentops.telegram_transport_harness_design_readiness"
READINESS_SCHEMA_VERSION = "0174UD_TELEGRAM_TRANSPORT_HARNESS_READINESS_V1"

SOURCE_BASELINE_COMMIT = "03e54bcceafb94309f74347d9a44c52578f10e74"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174UB_UC_UD")
PACKET_FILENAME = "telegram_transport_boundary_contract_packet.json"
DOC_FILENAME = "telegram_transport_boundary_contract.md"

NEXT_REQUIRED_GATE = (
    "an operator-owned live gate that, in one supervised operator session, "
    "hydrates the Telegram bot credential handle ONCE, runs a single read-only "
    "identity check ONCE, confirms the approved payload-hash binding, performs "
    "EXACTLY one supervised send, records the redacted response shape, and "
    "appends the immutable post-request audit; credential hydration, transport, "
    "and any live platform call remain operator-owned and are NOT enabled here"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174UE_UF_UG_TELEGRAM_OPERATOR_OWNED_LIVE_GATE_CREDENTIAL_"
    "HYDRATION_AND_SINGLE_SUPERVISED_SEND_EXECUTION_BATCH_V0"
)


# --------------------------------------------------------------------------- #
# Status vocabulary + reused provider facts (symbolic only)
# --------------------------------------------------------------------------- #
class Status:
    PASS = adapter.Status.PASS
    BLOCKED = adapter.Status.BLOCKED
    FAIL_CLOSED = adapter.Status.FAIL_CLOSED


PROVIDER_TELEGRAM = adapter.PROVIDER_TELEGRAM
METHOD_SUPERVISED_SEND = adapter.METHOD_SUPERVISED_SEND
METHOD_READ_ONLY_IDENTITY = adapter.METHOD_READ_ONLY_IDENTITY
INBOUND_METHODS_NOT_USED = adapter.INBOUND_METHODS_NOT_USED

# Symbolic redacted classes reused from the local adapter contract.
PROVIDER_CODE_CLASSES = adapter.PROVIDER_CODE_CLASSES
PROVIDER_CODE_UNKNOWN_CLASS = adapter.PROVIDER_CODE_UNKNOWN_CLASS
RESPONSE_STATUS_CLASSES = adapter.RESPONSE_STATUS_CLASSES
RESPONSE_STATUS_UNKNOWN_CLASS = adapter.RESPONSE_STATUS_UNKNOWN_CLASS
MESSAGE_ID_CLASSES = adapter.MESSAGE_ID_CLASSES
MESSAGE_ID_ABSENT_CLASS = adapter.MESSAGE_ID_ABSENT_CLASS

# Symbolic redacted bot-identity proof class (never a raw bot identity).
BOT_IDENTITY_REDACTED_CLASS = "bot_identity_redacted_class"
BOT_IDENTITY_NOT_PROVEN_CLASS = "bot_identity_not_proven_class"
BOT_IDENTITY_CLASSES = (BOT_IDENTITY_REDACTED_CLASS, BOT_IDENTITY_NOT_PROVEN_CLASS)

# Symbolic timestamp placeholder class (never a real timestamp value).
TIMESTAMP_PLACEHOLDER_CLASS = "future_operator_gate_timestamp_placeholder_class"

# The exact future execution order the harness DESIGNS but never performs.
FUTURE_EXECUTION_ORDER = (
    "hydrate_credential_handle_once",
    "run_read_only_identity_check_once",
    "confirm_approved_payload_hash_binding",
    "execute_exactly_one_send",
    "record_redacted_response_shape",
    "append_immutable_post_request_audit",
)

# Outcome classes.
BOUNDARY_DECLARED = "credential_boundary_declared_not_hydrated"
BOUNDARY_BLOCKED = "credential_boundary_blocked"
BOUNDARY_FAIL_CLOSED = "credential_boundary_fail_closed_forbidden_value"

IDENTITY_DECLARED = "identity_check_design_declared_not_run"
IDENTITY_BLOCKED = "identity_check_design_blocked"
IDENTITY_FAIL_CLOSED = "identity_check_design_fail_closed_forbidden_value"

HARNESS_BUILT = "telegram_single_send_harness_design_built_not_live"
HARNESS_BUILD_BLOCKED = "telegram_single_send_harness_design_blocked"
HARNESS_BUILD_FAIL_CLOSED = (
    "telegram_single_send_harness_design_fail_closed_forbidden_value")

AUDIT_DESIGNED = "post_request_audit_design_declared_not_live"
AUDIT_FAIL_CLOSED = "post_request_audit_design_fail_closed_forbidden_value"

READINESS_READY = "telegram_transport_harness_design_ready_not_live"
READINESS_BLOCKED = "telegram_transport_harness_design_blocked"
READINESS_FAIL_CLOSED = (
    "telegram_transport_harness_design_fail_closed_forbidden_value")

# Blocked-reason classes.
BLOCK_FORBIDDEN_VALUE = "transport_forbidden_value_detected"
BLOCK_FINANCIAL_ADVICE = "transport_financial_advice_detected"
BLOCK_OPERATOR_GATE_ID_MISSING = "operator_live_gate_id_missing"
BLOCK_CREDENTIAL_HANDLE_MISSING = "credential_handle_id_missing"
BLOCK_BOUNDARY_NOT_DECLARED = "credential_boundary_not_declared"
BLOCK_IDENTITY_DESIGN_MISSING = "read_only_identity_check_design_missing"
BLOCK_REQUEST_OBJECT_NOT_BUILT = "one_request_object_not_built"
BLOCK_PAYLOAD_HASH_BINDING_MISSING = "approved_payload_hash_binding_missing"
BLOCK_PAYLOAD_HASH_MISMATCH = "approved_payload_hash_binding_mismatch"
BLOCK_HARNESS_NOT_BUILT = "single_send_harness_design_not_built"

# R1-style upstream unsafe-behavior revalidation reasons.
BLOCK_BOUNDARY_UNSAFE_BEHAVIOR = "transport_boundary_unsafe_behavior_claimed"
BLOCK_IDENTITY_UNSAFE_BEHAVIOR = "transport_identity_unsafe_behavior_claimed"
BLOCK_REQUEST_UNSAFE_BEHAVIOR = "transport_request_unsafe_behavior_claimed"
BLOCK_HARNESS_UNSAFE_BEHAVIOR = "transport_harness_unsafe_behavior_claimed"

# Artifact-name labels passed to detect_unsafe_behavior_claims.
ARTIFACT_BOUNDARY = "boundary"
ARTIFACT_IDENTITY = "identity"
ARTIFACT_REQUEST = "request"
ARTIFACT_HARNESS = "harness"

_ARTIFACT_UNSAFE_BASE = {
    ARTIFACT_BOUNDARY: BLOCK_BOUNDARY_UNSAFE_BEHAVIOR,
    ARTIFACT_IDENTITY: BLOCK_IDENTITY_UNSAFE_BEHAVIOR,
    ARTIFACT_REQUEST: BLOCK_REQUEST_UNSAFE_BEHAVIOR,
    ARTIFACT_HARNESS: BLOCK_HARNESS_UNSAFE_BEHAVIOR,
}

# Universal unsafe-behavior flags that MUST be False on every consumed artifact.
_UNSAFE_BEHAVIOR_FLAGS = (
    "dispatch_performed",
    "live_request_performed",
    "platform_api_called",
    "telegram_api_called",
    "identity_check_performed",
    "credential_hydrated",
    "llm_behavior",
    "network_performed",
    "scheduler_enabled",
    "auto_retry_allowed",
    "autonomous_reply_performed",
    "dispatch_ready",
    "live_ready",
)

# Transport-specific readiness booleans that MUST be False where present.
_UNSAFE_READINESS_FLAGS = (
    "harness_is_dispatch",
    "harness_is_live_readiness",
    "harness_is_credential_hydration",
    "valid_for_live_execution",
)


# --------------------------------------------------------------------------- #
# Redaction + financial-advice scanning + deterministic serialization (reused).
# --------------------------------------------------------------------------- #
def scan_for_leaks(obj):
    """Return a sorted list of redaction violations (delegates upstream)."""
    return adapter.scan_for_leaks(obj)


def scan_for_financial_advice(obj):
    """Return a sorted list of financial-advice violations (delegates)."""
    return adapter.scan_for_financial_advice(obj)


def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Shared safety flags + R1 revalidation
# --------------------------------------------------------------------------- #
def _safety_flags():
    """Hard-coded safety invariants attached to every 0174UB/UC/UD object."""
    return {
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "telegram_api_called": False,
        "identity_check_performed": False,
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

    A consumed artifact (credential boundary, identity-check design, one-request
    object, or single-send harness) must NOT be able to carry a tampered flag
    claiming live/network/identity/credential/scheduler/retry/dispatch behavior
    past this transport boundary just because its status metadata still reads
    clear. This helper re-derives the truth directly from the flags.

    A universal flag "claims" unsafe behavior when it is present and not False.
    A transport-specific readiness boolean likewise blocks when present and not
    False. Returns a sorted, de-duplicated list whose first element (when any
    flag trips) is the artifact's bare unsafe-behavior-claimed class, followed
    by ``<base>:<flag>`` entries. An empty list means no unsafe behavior.
    """
    o = obj or {}
    base = _ARTIFACT_UNSAFE_BASE.get(
        artifact_name,
        "transport_" + str(artifact_name) + "_unsafe_behavior_claimed")
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
# 0174UB: TelegramCredentialBoundaryGate
# --------------------------------------------------------------------------- #
def declare_credential_boundary(*, operator_gate_id, credential_handle_id):
    """Declare the FUTURE credential-handle hydration step. Fail-closed.

    Symbolic only. Reads NO env / .env / keyring / credential file / browser
    session. Stores NO token, bot token, header, cookie, URL-with-token, raw
    chat id, username, or webhook URL -- only the symbolic operator gate id and
    credential handle id. The boundary stays
    ``credential_boundary_declared_not_hydrated``.

    Blocks when:

      * forbidden material => fail_closed;
      * the operator gate id is missing;
      * the credential handle id is missing.
    """
    scan_payload = {
        "operator_gate_id": operator_gate_id,
        "credential_handle_id": credential_handle_id,
    }
    if scan_for_leaks(scan_payload):
        return _boundary_result(
            BOUNDARY_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE],
            declared=False, forbidden_detected=True,
            operator_gate_id=operator_gate_id,
            credential_handle_id=credential_handle_id)

    blocked = []
    if not operator_gate_id:
        blocked.append(BLOCK_OPERATOR_GATE_ID_MISSING)
    if not credential_handle_id:
        blocked.append(BLOCK_CREDENTIAL_HANDLE_MISSING)

    declared = not blocked
    outcome = BOUNDARY_DECLARED if declared else BOUNDARY_BLOCKED
    return _boundary_result(
        outcome, blocked=sorted(set(blocked)), declared=declared,
        forbidden_detected=False, operator_gate_id=operator_gate_id,
        credential_handle_id=credential_handle_id)


def _boundary_result(outcome_class, *, blocked, declared, forbidden_detected,
                     operator_gate_id, credential_handle_id):
    """Build a deterministic TelegramCredentialBoundaryGate (pure value)."""
    status = (Status.PASS if declared
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "credential_boundary_schema": CREDENTIAL_BOUNDARY_SCHEMA,
        "credential_boundary_schema_version": CREDENTIAL_BOUNDARY_SCHEMA_VERSION,
        "status": status,
        "credential_boundary_outcome_class": outcome_class,
        "credential_boundary_declared": declared,
        "provider": PROVIDER_TELEGRAM,
        "operator_gate_id": operator_gate_id,
        "credential_handle_id": credential_handle_id,
        "credential_referenced_by_handle_only": True,
        "future_hydration_step_declared": True,
        # Explicit "reads no X" / "stores no X" invariants.
        "reads_env": False,
        "reads_dotenv_file": False,
        "reads_keyring": False,
        "reads_credential_file": False,
        "reads_browser_session": False,
        "stores_token": False,
        "stores_bot_token": False,
        "stores_header": False,
        "stores_cookie": False,
        "stores_url_with_token": False,
        "stores_raw_chat_id": False,
        "stores_username": False,
        "stores_webhook_url": False,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- the boundary is NEVER hydration / live.
        **_safety_flags(),
        "harness_is_dispatch": False,
        "harness_is_live_readiness": False,
        "harness_is_credential_hydration": False,
        "valid_for_live_execution": False,
    }
    result["credential_boundary_checksum"] = compute_checksum(result)
    return result


def _boundary_declared(boundary):
    b = boundary or {}
    return (
        b.get("credential_boundary_outcome_class") == BOUNDARY_DECLARED
        and b.get("credential_boundary_declared") is True
        and b.get("status") == Status.PASS
        and b.get("credential_hydrated") is False
    )


# --------------------------------------------------------------------------- #
# 0174UC: TelegramReadOnlyIdentityCheckDesign
# --------------------------------------------------------------------------- #
def design_read_only_identity_check(*, operator_gate_id):
    """Build a FUTURE-ONLY read-only identity-proof design. Fail-closed.

    Method is the symbolic read-only identity method (``getMe``). It runs NO
    request and performs NO network. Defines the expected REDACTED identity
    proof shape and stores NO provider response.

    Blocks when:

      * forbidden material => fail_closed;
      * the operator gate id is missing.
    """
    scan_payload = {"operator_gate_id": operator_gate_id}
    if scan_for_leaks(scan_payload):
        return _identity_result(
            IDENTITY_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE],
            declared=False, forbidden_detected=True,
            operator_gate_id=operator_gate_id)

    blocked = []
    if not operator_gate_id:
        blocked.append(BLOCK_OPERATOR_GATE_ID_MISSING)

    declared = not blocked
    outcome = IDENTITY_DECLARED if declared else IDENTITY_BLOCKED
    return _identity_result(
        outcome, blocked=sorted(set(blocked)), declared=declared,
        forbidden_detected=False, operator_gate_id=operator_gate_id)


def _identity_result(outcome_class, *, blocked, declared, forbidden_detected,
                     operator_gate_id):
    """Build a deterministic TelegramReadOnlyIdentityCheckDesign (pure value)."""
    status = (Status.PASS if declared
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    # Expected redacted identity-proof shape (FUTURE-ONLY; nothing is run).
    expected_identity_proof_shape = {
        "identity_check_not_run": True,
        "identity_check_future_operator_gate_required": True,
        "bot_identity_redacted_class": BOT_IDENTITY_NOT_PROVEN_CLASS,
        "provider_status_code_class": PROVIDER_CODE_UNKNOWN_CLASS,
        "response_checksum": None,
    }
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "identity_check_schema": IDENTITY_CHECK_SCHEMA,
        "identity_check_schema_version": IDENTITY_CHECK_SCHEMA_VERSION,
        "status": status,
        "identity_outcome_class": outcome_class,
        "identity_check_design_declared": declared,
        "provider": PROVIDER_TELEGRAM,
        "operator_gate_id": operator_gate_id,
        "is_future_only_design": True,
        "identity_method_name": METHOD_READ_ONLY_IDENTITY,
        "identity_method_is_read_only": True,
        "identity_check_not_run": True,
        "identity_check_future_operator_gate_required": True,
        "expected_identity_proof_shape": expected_identity_proof_shape,
        "bot_identity_classes": list(BOT_IDENTITY_CLASSES),
        "provider_status_code_classes": list(PROVIDER_CODE_CLASSES),
        "stores_raw_provider_response": False,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- the identity design is NEVER run / live.
        **_safety_flags(),
        "harness_is_dispatch": False,
        "harness_is_live_readiness": False,
        "harness_is_credential_hydration": False,
        "valid_for_live_execution": False,
    }
    result["identity_check_checksum"] = compute_checksum(result)
    return result


def _identity_present(identity_design):
    i = identity_design or {}
    return (
        i.get("identity_outcome_class") == IDENTITY_DECLARED
        and i.get("identity_check_design_declared") is True
        and i.get("status") == Status.PASS
        and i.get("identity_check_not_run") is True
    )


def _request_is_built(request_object):
    """Mirror the local adapter's built-request predicate (reused constants)."""
    r = request_object or {}
    return (
        r.get("one_request_outcome_class") == adapter.REQUEST_OK
        and r.get("one_request_built") is True
        and r.get("status") == adapter.Status.PASS
        and r.get("request_count_authorized") == 1
    )


def _request_payload_hash(request_object):
    """Return the send-text checksum bound into the built request object."""
    r = request_object or {}
    descriptor = r.get("request_descriptor") or {}
    return descriptor.get("send_text_checksum")


# --------------------------------------------------------------------------- #
# 0174UC: TelegramSingleSendExecutionHarnessDesign
# --------------------------------------------------------------------------- #
def design_single_send_harness(credential_boundary, identity_check_design,
                               one_request_object, *, operator_gate_id,
                               approved_payload_hash_binding):
    """Build a FUTURE-ONLY single-send execution harness design. Fail-closed.

    Consumes a built ``TelegramOneRequestObject``. Requires a declared
    credential boundary, a present identity-check design, a built request
    object, an operator live-gate id, and an approved payload-hash binding that
    matches the request's bound payload hash. States the EXACT future execution
    order but executes NOTHING; enables NO auto retry / scheduler / polling /
    webhook / reply automation.

    Blocks when:

      * forbidden material => fail_closed;
      * the credential boundary is not declared;
      * the identity-check design is missing;
      * the request object is not built;
      * the operator gate id is missing;
      * the approved payload-hash binding is missing or mismatched;
      * any consumed artifact claims unsafe behavior (R1).
    """
    cb = credential_boundary or {}
    ic = identity_check_design or {}
    ro = one_request_object or {}

    scan_payload = {
        "operator_gate_id": operator_gate_id,
        "approved_payload_hash_binding": approved_payload_hash_binding,
    }
    if scan_for_leaks([cb, ic, ro, scan_payload]):
        return _harness_result(
            HARNESS_BUILD_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE],
            built=False, forbidden_detected=True, credential_boundary=cb,
            identity_check_design=ic, one_request_object=ro,
            operator_gate_id=operator_gate_id,
            approved_payload_hash_binding=approved_payload_hash_binding)

    blocked = []
    if not _boundary_declared(cb):
        blocked.append(BLOCK_BOUNDARY_NOT_DECLARED)
    if not _identity_present(ic):
        blocked.append(BLOCK_IDENTITY_DESIGN_MISSING)
    if not _request_is_built(ro):
        blocked.append(BLOCK_REQUEST_OBJECT_NOT_BUILT)
    if not operator_gate_id:
        blocked.append(BLOCK_OPERATOR_GATE_ID_MISSING)

    if not approved_payload_hash_binding:
        blocked.append(BLOCK_PAYLOAD_HASH_BINDING_MISSING)
    else:
        bound = _request_payload_hash(ro)
        if bound is None or bound != approved_payload_hash_binding:
            blocked.append(BLOCK_PAYLOAD_HASH_MISMATCH)

    # R1 upstream safety-flag revalidation across consumed artifacts.
    blocked.extend(detect_unsafe_behavior_claims(cb, ARTIFACT_BOUNDARY))
    blocked.extend(detect_unsafe_behavior_claims(ic, ARTIFACT_IDENTITY))
    blocked.extend(detect_unsafe_behavior_claims(ro, ARTIFACT_REQUEST))

    built = not blocked
    outcome = HARNESS_BUILT if built else HARNESS_BUILD_BLOCKED
    return _harness_result(
        outcome, blocked=sorted(set(blocked)), built=built,
        forbidden_detected=False, credential_boundary=cb,
        identity_check_design=ic, one_request_object=ro,
        operator_gate_id=operator_gate_id,
        approved_payload_hash_binding=approved_payload_hash_binding)


def _harness_result(outcome_class, *, blocked, built, forbidden_detected,
                    credential_boundary, identity_check_design,
                    one_request_object, operator_gate_id,
                    approved_payload_hash_binding):
    """Build a deterministic TelegramSingleSendExecutionHarnessDesign value."""
    status = (Status.PASS if built
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    cb = credential_boundary or {}
    ic = identity_check_design or {}
    ro = one_request_object or {}
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "harness_schema": HARNESS_SCHEMA,
        "harness_schema_version": HARNESS_SCHEMA_VERSION,
        "status": status,
        "harness_outcome_class": outcome_class,
        "single_send_harness_design_built": built,
        "is_future_only_design": True,
        "provider": PROVIDER_TELEGRAM,
        "operator_gate_id": operator_gate_id,
        "credential_handle_id": cb.get("credential_handle_id"),
        "destination_binding_id": ro.get("destination_binding_id"),
        "identity_method_name": ic.get("identity_method_name"),
        "supervised_send_method": METHOD_SUPERVISED_SEND,
        "approved_payload_hash_binding": approved_payload_hash_binding,
        "future_execution_order": list(FUTURE_EXECUTION_ORDER),
        "authorizes_exactly_one_future_send": built,
        "future_send_count_authorized": 1 if built else 0,
        "send_performed": False,
        "identity_check_performed": False,
        # Explicit "no automation" invariants.
        "auto_retry_allowed": False,
        "scheduler_enabled": False,
        "polling_enabled": False,
        "webhook_registered": False,
        "reply_automation_enabled": False,
        "inbound_methods_not_used": list(INBOUND_METHODS_NOT_USED),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- the harness is NEVER dispatch / live.
        **_safety_flags(),
        "harness_is_dispatch": False,
        "harness_is_live_readiness": False,
        "harness_is_credential_hydration": False,
        "valid_for_live_execution": False,
    }
    result["harness_checksum"] = compute_checksum(result)
    return result


def _harness_built(harness_design):
    h = harness_design or {}
    return (
        h.get("harness_outcome_class") == HARNESS_BUILT
        and h.get("single_send_harness_design_built") is True
        and h.get("status") == Status.PASS
        and h.get("future_send_count_authorized") == 1
    )


# --------------------------------------------------------------------------- #
# 0174UD: PostRequestAuditDesign (FUTURE-ONLY)
# --------------------------------------------------------------------------- #
def design_post_request_audit(*, operator_gate_id, request_checksum=None,
                              response_checksum=None,
                              provider_status_class=RESPONSE_STATUS_UNKNOWN_CLASS,
                              redacted_message_id_class=MESSAGE_ID_ABSENT_CLASS,
                              timestamp_placeholder_class=TIMESTAMP_PLACEHOLDER_CLASS):
    """Build a FUTURE-ONLY post-request audit shape. Fail-closed.

    Stores ONLY symbolic request/response checksums, a provider status class, a
    redacted message-id class, the operator gate id, and a timestamp placeholder
    class. It stores NO raw response/header/cookie/token/chat id/url. Unknown
    symbolic classes are coerced to the explicit unknown/absent class.
    """
    blocked = []
    scan_payload = {
        "operator_gate_id": operator_gate_id,
        "request_checksum": request_checksum,
        "response_checksum": response_checksum,
        "provider_status_class": provider_status_class,
        "redacted_message_id_class": redacted_message_id_class,
        "timestamp_placeholder_class": timestamp_placeholder_class,
    }
    forbidden_detected = bool(scan_for_leaks(scan_payload))
    if forbidden_detected:
        blocked.append(BLOCK_FORBIDDEN_VALUE)

    status_class = (provider_status_class
                    if provider_status_class in RESPONSE_STATUS_CLASSES
                    else RESPONSE_STATUS_UNKNOWN_CLASS)
    msg_class = (redacted_message_id_class
                 if redacted_message_id_class in MESSAGE_ID_CLASSES
                 else MESSAGE_ID_ABSENT_CLASS)

    status = Status.FAIL_CLOSED if forbidden_detected else Status.PASS
    outcome = AUDIT_FAIL_CLOSED if forbidden_detected else AUDIT_DESIGNED
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "audit_schema": AUDIT_SCHEMA,
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "status": status,
        "audit_outcome_class": outcome,
        "is_future_only_shape": True,
        "provider": PROVIDER_TELEGRAM,
        "operator_gate_id": operator_gate_id,
        "request_checksum": request_checksum,
        "response_checksum": response_checksum,
        "provider_status_class": status_class,
        "redacted_message_id_class": msg_class,
        "timestamp_placeholder_class": timestamp_placeholder_class,
        "provider_status_classes": list(RESPONSE_STATUS_CLASSES),
        "message_id_classes": list(MESSAGE_ID_CLASSES),
        # Explicit "stores no raw X" invariants.
        "stores_raw_provider_response": False,
        "stores_header": False,
        "stores_cookie": False,
        "stores_token": False,
        "stores_raw_chat_id": False,
        "stores_url": False,
        "blocked_reasons": sorted(set(blocked)),
        "forbidden_fields_detected": forbidden_detected,
        **_safety_flags(),
        "harness_is_dispatch": False,
        "harness_is_live_readiness": False,
        "harness_is_credential_hydration": False,
        "valid_for_live_execution": False,
    }
    result["audit_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# 0174UD: Transport-harness readiness classifier
# --------------------------------------------------------------------------- #
def classify_transport_harness_design_readiness(
        credential_boundary, identity_check_design, one_request_object,
        single_send_harness_design, *, audit_design=None):
    """Classify the transport-harness DESIGN readiness. Fail-closed. NEVER live.

    Returns ``telegram_transport_harness_design_ready_not_live`` only when ALL
    hold:

      * no forbidden material and no financial advice in any consumed artifact;
      * the credential boundary is declared (and not hydrated);
      * the read-only identity-check design is present (and not run);
      * the one-request object is built with exactly one authorized request;
      * the single-send harness design is built;
      * no consumed artifact claims unsafe behavior (R1 revalidation).

    The result is NEVER ``live_ready`` and NEVER ``valid_for_live_execution``;
    it always ``requires_operator_live_gate``.
    """
    cb = credential_boundary or {}
    ic = identity_check_design or {}
    ro = one_request_object or {}
    hd = single_send_harness_design or {}
    au = audit_design or {}
    blocked = []

    consumed = [cb, ic, ro, hd, au]
    if scan_for_leaks(consumed):
        return _readiness_result(
            READINESS_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE],
            ready=False, forbidden_detected=True, financial_detected=False,
            credential_boundary=cb, identity_check_design=ic,
            one_request_object=ro, single_send_harness_design=hd,
            audit_design=au)

    if scan_for_financial_advice(consumed):
        return _readiness_result(
            READINESS_FAIL_CLOSED, blocked=[BLOCK_FINANCIAL_ADVICE],
            ready=False, forbidden_detected=False, financial_detected=True,
            credential_boundary=cb, identity_check_design=ic,
            one_request_object=ro, single_send_harness_design=hd,
            audit_design=au)

    if not _boundary_declared(cb):
        blocked.append(BLOCK_BOUNDARY_NOT_DECLARED)
    if not _identity_present(ic):
        blocked.append(BLOCK_IDENTITY_DESIGN_MISSING)
    if not _request_is_built(ro):
        blocked.append(BLOCK_REQUEST_OBJECT_NOT_BUILT)
    if not _harness_built(hd):
        blocked.append(BLOCK_HARNESS_NOT_BUILT)

    # R1 upstream safety-flag revalidation across consumed artifacts.
    blocked.extend(detect_unsafe_behavior_claims(cb, ARTIFACT_BOUNDARY))
    blocked.extend(detect_unsafe_behavior_claims(ic, ARTIFACT_IDENTITY))
    blocked.extend(detect_unsafe_behavior_claims(ro, ARTIFACT_REQUEST))
    blocked.extend(detect_unsafe_behavior_claims(hd, ARTIFACT_HARNESS))

    ready = not blocked
    outcome = READINESS_READY if ready else READINESS_BLOCKED
    return _readiness_result(
        outcome, blocked=sorted(set(blocked)), ready=ready,
        forbidden_detected=False, financial_detected=False,
        credential_boundary=cb, identity_check_design=ic,
        one_request_object=ro, single_send_harness_design=hd, audit_design=au)


def _readiness_result(outcome_class, *, blocked, ready, forbidden_detected,
                      financial_detected, credential_boundary,
                      identity_check_design, one_request_object,
                      single_send_harness_design, audit_design):
    """Build a deterministic transport-harness readiness classification."""
    if forbidden_detected or financial_detected:
        status = Status.FAIL_CLOSED
    elif ready:
        status = Status.PASS
    else:
        status = Status.BLOCKED
    hd = single_send_harness_design or {}
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "readiness_schema": READINESS_SCHEMA,
        "readiness_schema_version": READINESS_SCHEMA_VERSION,
        "status": status,
        "transport_harness_readiness_outcome_class": outcome_class,
        "telegram_transport_harness_design_ready_not_live": ready,
        "provider": PROVIDER_TELEGRAM,
        "future_execution_order": list(FUTURE_EXECUTION_ORDER),
        "future_send_count_authorized": hd.get("future_send_count_authorized")
        if hd else None,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_detected,
        "requires_operator_live_gate": True,
        # Hard invariants -- the harness design is NEVER live.
        **_safety_flags(),
        "harness_is_dispatch": False,
        "harness_is_live_readiness": False,
        "harness_is_credential_hydration": False,
        "valid_for_live_execution": False,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    result["transport_harness_readiness_checksum"] = compute_checksum(result)
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
        "credential_boundary_schema": CREDENTIAL_BOUNDARY_SCHEMA,
        "credential_boundary_schema_version": CREDENTIAL_BOUNDARY_SCHEMA_VERSION,
        "identity_check_schema": IDENTITY_CHECK_SCHEMA,
        "identity_check_schema_version": IDENTITY_CHECK_SCHEMA_VERSION,
        "harness_schema": HARNESS_SCHEMA,
        "harness_schema_version": HARNESS_SCHEMA_VERSION,
        "audit_schema": AUDIT_SCHEMA,
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "readiness_schema": READINESS_SCHEMA,
        "readiness_schema_version": READINESS_SCHEMA_VERSION,
        "provider": PROVIDER_TELEGRAM,
        "supervised_send_method": METHOD_SUPERVISED_SEND,
        "read_only_identity_method": METHOD_READ_ONLY_IDENTITY,
        "inbound_methods_not_used": list(INBOUND_METHODS_NOT_USED),
        "future_execution_order": list(FUTURE_EXECUTION_ORDER),
        "bot_identity_classes": list(BOT_IDENTITY_CLASSES),
        "provider_status_code_classes": list(PROVIDER_CODE_CLASSES),
        "response_status_classes": list(RESPONSE_STATUS_CLASSES),
        "message_id_classes": list(MESSAGE_ID_CLASSES),
        "timestamp_placeholder_class": TIMESTAMP_PLACEHOLDER_CLASS,
        "credential_boundary_outcome_classes": [
            BOUNDARY_DECLARED, BOUNDARY_BLOCKED, BOUNDARY_FAIL_CLOSED,
        ],
        "identity_outcome_classes": [
            IDENTITY_DECLARED, IDENTITY_BLOCKED, IDENTITY_FAIL_CLOSED,
        ],
        "harness_outcome_classes": [
            HARNESS_BUILT, HARNESS_BUILD_BLOCKED, HARNESS_BUILD_FAIL_CLOSED,
        ],
        "audit_outcome_classes": [AUDIT_DESIGNED, AUDIT_FAIL_CLOSED],
        "transport_harness_readiness_outcome_classes": [
            READINESS_READY, READINESS_BLOCKED, READINESS_FAIL_CLOSED,
        ],
        "r1_upstream_revalidation_blocked_reasons": [
            BLOCK_BOUNDARY_UNSAFE_BEHAVIOR,
            BLOCK_IDENTITY_UNSAFE_BEHAVIOR,
            BLOCK_REQUEST_UNSAFE_BEHAVIOR,
            BLOCK_HARNESS_UNSAFE_BEHAVIOR,
        ],
        "r1_revalidated_unsafe_flags": list(
            _UNSAFE_BEHAVIOR_FLAGS + _UNSAFE_READINESS_FLAGS),
        "hard_invariants": [
            "real_core_transport_design_but_never_live",
            "credential_boundary_declared_not_hydrated",
            "credential_referenced_by_handle_only",
            "boundary_reads_no_env_keyring_dotenv_credential_file_or_session",
            "boundary_stores_no_token_header_cookie_url_chat_username_webhook",
            "identity_check_is_get_me_symbolic_only_and_not_run",
            "identity_design_stores_no_provider_response",
            "harness_consumes_built_one_request_object",
            "harness_declares_exact_future_execution_order",
            "harness_authorizes_exactly_one_future_send_but_performs_none",
            "harness_enables_no_retry_scheduler_polling_webhook_reply",
            "audit_is_future_only",
            "audit_stores_no_raw_response_header_cookie_token_chat_id_url",
            "payload_hash_binding_must_match_request",
            "inbound_receiving_still_absent",
            "harness_is_not_dispatch",
            "harness_is_not_live_readiness",
            "harness_is_not_credential_hydration",
            "harness_requires_operator_owned_live_gate",
            "unsafe_upstream_behavior_claim_blocks_harness",
            "no_credential_hydration",
            "no_platform_api",
            "no_telegram_send",
            "no_identity_check_execution",
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
    order = "\n".join(
        f"  {i}. `{step}`"
        for i, step in enumerate(packet["future_execution_order"], start=1))
    hard = "\n".join(f"  * `{inv}`" for inv in packet["hard_invariants"])
    r1_reasons = "\n".join(
        f"  * `{r}`"
        for r in packet["r1_upstream_revalidation_blocked_reasons"])
    return (
        f"# 0174UB/UC/UD Telegram Transport Boundary + Single-Send Harness "
        f"Design\n\n"
        f"Task: `{TASK_LABEL}`\n\n"
        f"Model: `{MODEL}` version `{MODEL_VERSION}`\n\n"
        f"Baseline commit: `{SOURCE_BASELINE_COMMIT}`\n\n"
        f"## Role\n\n"
        f"This batch is LOCAL, deterministic, and REAL CORE TRANSPORT-BOUNDARY "
        f"DESIGN that is NEVER LIVE. It performs NO network call, NO live "
        f"platform API call, NO supervised send, NO `{METHOD_READ_ONLY_IDENTITY}` "
        f"identity-check execution, NO env/credential read, NO credential "
        f"hydration, NO scheduler, NO retry loop, and NO webhook/polling. It "
        f"NEVER dispatches.\n\n"
        f"## 0174UB TelegramCredentialBoundaryGate\n\n"
        f"Declares -- symbolically only -- the FUTURE credential-handle "
        f"hydration step. Requires an explicit operator gate id and credential "
        f"handle id. Reads NO env / .env / keyring / credential file / browser "
        f"session and stores NO token, bot token, header, cookie, "
        f"URL-with-token, raw chat id, username, or webhook URL. It stays "
        f"`{BOUNDARY_DECLARED}`.\n\n"
        f"## 0174UC Read-only identity check + single-send harness design\n\n"
        f"The identity-check design is FUTURE-ONLY: the method is the symbolic "
        f"`{METHOD_READ_ONLY_IDENTITY}`, no request is run, no network is "
        f"performed, and no provider response is stored. The single-send "
        f"harness design consumes a built one-request object and states the "
        f"EXACT future execution order:\n\n{order}\n\n"
        f"It authorizes EXACTLY one future send but performs none, and enables "
        f"no auto retry / scheduler / polling / webhook / reply automation.\n\n"
        f"## 0174UD Post-request audit design + readiness classifier\n\n"
        f"The post-request audit shape is FUTURE-ONLY and stores only symbolic "
        f"request/response checksums, a provider status class, a redacted "
        f"message-id class, the operator gate id, and a timestamp placeholder "
        f"class (`{TIMESTAMP_PLACEHOLDER_CLASS}`). It stores NO raw "
        f"response/header/cookie/token/chat id/url. The readiness classifier "
        f"returns `{READINESS_READY}` / `{READINESS_BLOCKED}` / "
        f"`{READINESS_FAIL_CLOSED}` and is NEVER `live_ready` and NEVER "
        f"`valid_for_live_execution`.\n\n"
        f"## R1 upstream safety-flag revalidation\n\n"
        f"The transport boundary re-derives upstream safety truth directly "
        f"from the flags on every consumed artifact (credential boundary, "
        f"identity-check design, one-request object, single-send harness). A "
        f"`pass` status can NOT hide a tampered claim of "
        f"network/platform/Telegram/identity/credential/LLM/scheduler/retry/"
        f"dispatch or live-readiness behavior; any such claim blocks:\n\n"
        f"{r1_reasons}\n\n"
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
