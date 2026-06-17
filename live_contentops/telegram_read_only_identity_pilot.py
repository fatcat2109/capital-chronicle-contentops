"""Telegram operator-owned credential + read-only ``getMe`` identity pilot.

Tasks 0174UE (operator-owned credential hydration boundary), 0174UF (read-only
``getMe`` identity-proof pilot with strict allowlist + budget 1), and 0174UG
(redacted identity proof + immutable identity-pilot audit packet) -- the FIRST
controlled, live-capable read-only Telegram step on top of the accepted chain:

  * 0174TV/TW/TX provider live-gate design.
  * 0174TY/TZ/UA Telegram local adapter + one-request builder.
  * 0174UB/UC/UD Telegram transport boundary + single-send harness design.

This is NOT a posting task. There is NO ``sendMessage`` anywhere in this batch.
The ONLY platform method this module recognises is the read-only identity
method ``getMe``. The ONLY env variable it will ever read is
``CAPITAL_CHRONICLE_TELEGRAM_BOT_TOKEN`` -- and ONLY when the operator passes
``operator_live_read_only_enabled=True``.

DEFAULT POSTURE (no arguments enabling live):
  * dry-run only -- NO env read, NO network, NO credential hydration;
  * ``execute_read_only_identity_pilot`` returns ``identity_pilot_not_run_dry_run_only``.

CONTROLLED LIVE READ-ONLY POSTURE (operator_live_read_only_enabled=True):
  * reads ONLY the one allowed env var name; if absent => blocked credential_missing;
  * hydrates a REDACTED credential proof (fingerprint hash + length class only) --
    the raw token is NEVER returned, logged, or persisted;
  * performs EXACTLY one ``getMe`` request to ``https://api.telegram.org`` with a
    short explicit timeout, NO retry, NO scheduler, NO webhook, NO polling;
  * redacts the response to symbolic classes + checksums; NEVER stores the raw
    body, raw bot id, raw username, raw URL with token, headers, or cookies.

HARD GUARANTEES (enforced by tests + leakage guards):
  * stdlib only. ``os`` and ``urllib`` are imported LAZILY inside the gated
    functions, never at import time, and the real network path runs ONLY under
    the explicit operator live flag. In automated tests an injected mock
    transport is used; NO real network call is made.
  * NO ``sendMessage``, NO posting, NO Telegram write method, NO
    ``getUpdates``/``setWebhook``, NO webhook/polling, NO auto retry, NO
    scheduler, NO autonomous reply/DM.
  * NO ``.env`` / credential-file read. NO arbitrary environment scan -- exactly
    one explicit variable name, and only when live is enabled.
  * NO raw token or raw response persistence. Redaction runs on every emitted
    artifact. NO financial advice / signal framing.

Importing this module performs NO writes, NO env reads, and NO network. Artifacts
are written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path

# Reuse the accepted adapter's scanners + deterministic serialization + symbolic
# redacted vocabulary and verified provider facts. No risky literal is
# re-declared here. NOTE: top-level imports are stdlib-hashing/json + the local
# contract only -- NOT os.environ and NOT urllib (both are lazy + gated below).
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = (
    "TASK_CONTENTOPS_0174UE_UF_UG_TELEGRAM_OPERATOR_OWNED_CREDENTIAL_AND_"
    "READ_ONLY_IDENTITY_PILOT_BATCH_V0"
)
MODEL = "TELEGRAM_READ_ONLY_IDENTITY_PILOT_0174UE_UF_UG"
MODEL_VERSION = "0174UE_UF_UG_TELEGRAM_READ_ONLY_IDENTITY_PILOT_V1"

REQUEST_PLAN_SCHEMA = "contentops.telegram_identity_pilot_request_plan"
REQUEST_PLAN_SCHEMA_VERSION = "0174UE_TELEGRAM_IDENTITY_PILOT_REQUEST_PLAN_V1"
CREDENTIAL_PROOF_SCHEMA = "contentops.telegram_credential_hydration_proof"
CREDENTIAL_PROOF_SCHEMA_VERSION = "0174UE_TELEGRAM_CREDENTIAL_HYDRATION_PROOF_V1"
IDENTITY_PROOF_SCHEMA = "contentops.telegram_redacted_identity_proof"
IDENTITY_PROOF_SCHEMA_VERSION = "0174UF_TELEGRAM_REDACTED_IDENTITY_PROOF_V1"
AUDIT_SCHEMA = "contentops.telegram_identity_pilot_audit_packet"
AUDIT_SCHEMA_VERSION = "0174UG_TELEGRAM_IDENTITY_PILOT_AUDIT_PACKET_V1"

SOURCE_BASELINE_COMMIT = "824352c99eecf9c1e463250a5226d4bb68ba6c71"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174UE_UF_UG")
PACKET_FILENAME = "telegram_read_only_identity_pilot_packet.json"
DOC_FILENAME = "telegram_read_only_identity_pilot.md"

# --------------------------------------------------------------------------- #
# Strict policy constants
# --------------------------------------------------------------------------- #
# The ONLY environment variable name this module will ever read, and ONLY when
# the operator explicitly enables the live read-only pilot.
ALLOWED_ENV_VAR = "CAPITAL_CHRONICLE_TELEGRAM_BOT_TOKEN"

# The ONLY allowed host + method. ``getMe`` is read-only identity; reused from
# the accepted design facts so no fresh literal is introduced.
ALLOWED_HOST = "https://" + adapter.TELEGRAM_API_HOST
ALLOWED_METHOD = adapter.METHOD_READ_ONLY_IDENTITY  # "getMe"
REQUEST_BUDGET = 1
REQUEST_TIMEOUT_SECONDS = 10

# Methods that are categorically forbidden in this read-only pilot. The
# supervised-send + inbound-receiving method names are reused from the design
# facts (data, not fresh literals).
FORBIDDEN_METHODS = tuple(sorted(set(
    (adapter.METHOD_SUPERVISED_SEND,) + tuple(adapter.INBOUND_METHODS_NOT_USED)
)))

PROVIDER_TELEGRAM = adapter.PROVIDER_TELEGRAM

# Reused symbolic redacted classes.
RESPONSE_STATUS_OK_CLASS = adapter.RESPONSE_STATUS_OK_CLASS
RESPONSE_STATUS_ERROR_CLASS = adapter.RESPONSE_STATUS_ERROR_CLASS
RESPONSE_STATUS_UNKNOWN_CLASS = adapter.RESPONSE_STATUS_UNKNOWN_CLASS
RESPONSE_STATUS_CLASSES = adapter.RESPONSE_STATUS_CLASSES

PROVIDER_CODE_SUCCESS_CLASS = adapter.PROVIDER_CODE_SUCCESS_CLASS
PROVIDER_CODE_CLIENT_ERROR_CLASS = adapter.PROVIDER_CODE_CLIENT_ERROR_CLASS
PROVIDER_CODE_SERVER_ERROR_CLASS = adapter.PROVIDER_CODE_SERVER_ERROR_CLASS
PROVIDER_CODE_UNKNOWN_CLASS = adapter.PROVIDER_CODE_UNKNOWN_CLASS
PROVIDER_CODE_CLASSES = adapter.PROVIDER_CODE_CLASSES

# Redacted bot identity / username classes (presence only, never raw values).
BOT_IDENTITY_PRESENT_CLASS = "bot_identity_redacted_present_class"
BOT_IDENTITY_ABSENT_CLASS = "bot_identity_redacted_absent_class"
BOT_IDENTITY_CLASSES = (BOT_IDENTITY_PRESENT_CLASS, BOT_IDENTITY_ABSENT_CLASS)
BOT_USERNAME_PRESENT_CLASS = "bot_username_redacted_present_class"
BOT_USERNAME_ABSENT_CLASS = "bot_username_redacted_absent_class"
BOT_USERNAME_CLASSES = (BOT_USERNAME_PRESENT_CLASS, BOT_USERNAME_ABSENT_CLASS)

# Symbolic timestamp placeholder class (never a real timestamp value persisted).
TIMESTAMP_PLACEHOLDER_CLASS = "identity_pilot_timestamp_placeholder_class"

# Credential proof classes.
CREDENTIAL_PROOF_OK = "credential_hydration_proof_ok_redacted"
CREDENTIAL_PROOF_NOT_HYDRATED = "credential_not_hydrated_dry_run_only"
CREDENTIAL_PROOF_BLOCKED = "credential_hydration_blocked"
CREDENTIAL_PROOF_FAIL_CLOSED = "credential_hydration_fail_closed_forbidden_value"

# Request-plan classes.
PLAN_BUILT = "identity_pilot_request_plan_built"
PLAN_BLOCKED = "identity_pilot_request_plan_blocked"
PLAN_FAIL_CLOSED = "identity_pilot_request_plan_fail_closed_forbidden_value"

# Identity-proof / pilot-execution classes.
PILOT_NOT_RUN_DRY_RUN = "identity_pilot_not_run_dry_run_only"
PILOT_OK = "identity_pilot_getme_ok_redacted"
PILOT_PROVIDER_ERROR = "identity_pilot_getme_provider_error_redacted"
PILOT_NETWORK_BLOCKED = "identity_pilot_getme_network_blocked_redacted"
PILOT_BLOCKED = "identity_pilot_blocked"
PILOT_FAIL_CLOSED = "identity_pilot_fail_closed_forbidden_value"

# Audit classes.
AUDIT_RECORDED = "identity_pilot_audit_recorded"
AUDIT_FAIL_CLOSED = "identity_pilot_audit_fail_closed_forbidden_value"

# Blocked-reason classes.
BLOCK_FORBIDDEN_VALUE = "identity_pilot_forbidden_value_detected"
BLOCK_FINANCIAL_ADVICE = "identity_pilot_financial_advice_detected"
BLOCK_OPERATOR_GATE_ID_MISSING = "operator_gate_id_missing"
BLOCK_METHOD_NOT_GET_ME = "method_is_not_read_only_get_me"
BLOCK_FORBIDDEN_METHOD_REQUESTED = "forbidden_method_requested"
BLOCK_HOST_NOT_ALLOWED = "host_not_allowed"
BLOCK_BUDGET_NOT_ONE = "request_budget_not_exactly_one"
BLOCK_TIMEOUT_INVALID = "request_timeout_invalid"
BLOCK_RETRY_REQUESTED = "auto_retry_requested"
BLOCK_SCHEDULER_REQUESTED = "scheduler_requested"
BLOCK_WEBHOOK_REQUESTED = "webhook_requested"
BLOCK_POLLING_REQUESTED = "polling_requested"
BLOCK_CREDENTIAL_MISSING = "credential_missing"
BLOCK_CREDENTIAL_SUSPICIOUS_SHAPE = "credential_suspicious_shape_redacted"
BLOCK_LIVE_NOT_ENABLED = "operator_live_read_only_not_enabled"
BLOCK_PLAN_NOT_BUILT = "request_plan_not_built"
BLOCK_CREDENTIAL_PROOF_NOT_OK = "credential_proof_not_ok"


# --------------------------------------------------------------------------- #
# Status + scanning + serialization (reused from the accepted adapter)
# --------------------------------------------------------------------------- #
class Status:
    PASS = adapter.Status.PASS
    BLOCKED = adapter.Status.BLOCKED
    FAIL_CLOSED = adapter.Status.FAIL_CLOSED


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


def _safety_flags():
    """Hard-coded safety invariants on every 0174UE/UF/UG object.

    Note these describe what THIS module never autonomously does. A live
    read-only ``getMe`` may set ``network_performed``/``read_only_request_performed``
    True on the identity-proof object ONLY when the operator explicitly enabled
    it; the send/post/reply/scheduler invariants are ALWAYS False.
    """
    return {
        "sendmessage_performed": False,
        "posting_performed": False,
        "platform_write_performed": False,
        "autonomous_reply_performed": False,
        "inbound_receiving_performed": False,
        "scheduler_enabled": False,
        "auto_retry_allowed": False,
        "webhook_registered": False,
        "polling_enabled": False,
        "llm_behavior": False,
        "no_financial_advice_emitted": True,
        "valid_for_live_execution": False,
    }


# --------------------------------------------------------------------------- #
# Redacted credential fingerprint (NEVER the token)
# --------------------------------------------------------------------------- #
def _length_class(n):
    """Bucket a length into a symbolic class so no exact secret length leaks."""
    if n <= 0:
        return "len_class_empty"
    if n < 20:
        return "len_class_short"
    if n < 40:
        return "len_class_medium"
    if n < 60:
        return "len_class_standard"
    return "len_class_long"


def _credential_fingerprint(token):
    """Return a salted, truncated fingerprint of the token. NEVER the token.

    Uses a fixed domain-separation salt + SHA-256, then keeps only a short hex
    prefix. This is a one-way presence/equality fingerprint; the raw token can
    not be recovered and its exact length is bucketed, not exposed.
    """
    digest = hashlib.sha256(
        ("cc_identity_pilot_v1::" + token).encode("utf-8")).hexdigest()
    return digest[:16]


def _looks_suspicious(token):
    """Heuristic shape check. Returns True if the value does not look like a
    plausible bot token. Used ONLY to emit a redacted reason -- never the value.

    A plausible Telegram bot token looks like ``<digits>:<alphanumeric/-_>`` with
    a reasonably long secret body. We do NOT persist or echo the token in any
    branch.
    """
    if not token or not isinstance(token, str):
        return True
    if ":" not in token:
        return True
    numeric_id, _, secret = token.partition(":")
    if not numeric_id.isdigit():
        return True
    if len(secret) < 20:
        return True
    return False


# --------------------------------------------------------------------------- #
# 0174UE: request plan
# --------------------------------------------------------------------------- #
def build_identity_pilot_request_plan(*, operator_gate_id,
                                      operator_live_read_only_enabled=False,
                                      requested_method=ALLOWED_METHOD,
                                      requested_host=ALLOWED_HOST,
                                      request_budget=REQUEST_BUDGET,
                                      timeout_seconds=REQUEST_TIMEOUT_SECONDS,
                                      auto_retry=False, scheduler=False,
                                      webhook=False, polling=False):
    """Build + validate the read-only identity-pilot request plan. Fail-closed.

    Dry-run by default. No token hydration is declared unless the operator
    explicitly enables the live read-only pilot. Blocks:

      * forbidden material => fail_closed;
      * a missing operator gate id;
      * any method other than ``getMe`` / any explicitly forbidden method;
      * a host other than the allowed Telegram host;
      * a request budget other than exactly 1;
      * a non-positive / oversized timeout;
      * any auto retry / scheduler / webhook / polling request.
    """
    scan_payload = {
        "operator_gate_id": operator_gate_id,
        "requested_method": requested_method,
        "requested_host": requested_host,
    }
    if scan_for_leaks(scan_payload):
        return _plan_result(
            PLAN_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE], built=False,
            forbidden_detected=True, operator_gate_id=operator_gate_id,
            live_enabled=bool(operator_live_read_only_enabled),
            requested_method=requested_method, requested_host=requested_host,
            request_budget=request_budget, timeout_seconds=timeout_seconds)

    blocked = []
    if not operator_gate_id:
        blocked.append(BLOCK_OPERATOR_GATE_ID_MISSING)
    if requested_method in FORBIDDEN_METHODS:
        blocked.append(BLOCK_FORBIDDEN_METHOD_REQUESTED)
    if requested_method != ALLOWED_METHOD:
        blocked.append(BLOCK_METHOD_NOT_GET_ME)
    if requested_host != ALLOWED_HOST:
        blocked.append(BLOCK_HOST_NOT_ALLOWED)
    if request_budget != REQUEST_BUDGET:
        blocked.append(BLOCK_BUDGET_NOT_ONE)
    if not isinstance(timeout_seconds, int) or timeout_seconds <= 0 \
            or timeout_seconds > 30:
        blocked.append(BLOCK_TIMEOUT_INVALID)
    if auto_retry:
        blocked.append(BLOCK_RETRY_REQUESTED)
    if scheduler:
        blocked.append(BLOCK_SCHEDULER_REQUESTED)
    if webhook:
        blocked.append(BLOCK_WEBHOOK_REQUESTED)
    if polling:
        blocked.append(BLOCK_POLLING_REQUESTED)

    built = not blocked
    outcome = PLAN_BUILT if built else PLAN_BLOCKED
    return _plan_result(
        outcome, blocked=sorted(set(blocked)), built=built,
        forbidden_detected=False, operator_gate_id=operator_gate_id,
        live_enabled=bool(operator_live_read_only_enabled),
        requested_method=requested_method, requested_host=requested_host,
        request_budget=request_budget, timeout_seconds=timeout_seconds)


def _plan_result(outcome_class, *, blocked, built, forbidden_detected,
                 operator_gate_id, live_enabled, requested_method,
                 requested_host, request_budget, timeout_seconds):
    """Build a deterministic request plan (pure value)."""
    status = (Status.PASS if built
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "request_plan_schema": REQUEST_PLAN_SCHEMA,
        "request_plan_schema_version": REQUEST_PLAN_SCHEMA_VERSION,
        "status": status,
        "request_plan_outcome_class": outcome_class,
        "request_plan_built": built,
        "provider": PROVIDER_TELEGRAM,
        "operator_gate_id": operator_gate_id,
        "operator_live_read_only_enabled": live_enabled,
        "mode": "live_read_only" if live_enabled else "dry_run_only",
        "allowed_host": ALLOWED_HOST,
        "allowed_method": ALLOWED_METHOD,
        "requested_method": requested_method,
        "requested_host": requested_host,
        "request_budget": request_budget,
        "request_budget_authorized": REQUEST_BUDGET,
        "timeout_seconds": timeout_seconds,
        "forbidden_methods": list(FORBIDDEN_METHODS),
        "token_hydration_declared": bool(live_enabled) and built,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        **_safety_flags(),
        # The plan itself performs nothing.
        "network_performed": False,
        "read_only_request_performed": False,
        "credential_hydrated": False,
    }
    result["request_plan_checksum"] = compute_checksum(result)
    return result


def _plan_built(plan):
    p = plan or {}
    return (
        p.get("request_plan_outcome_class") == PLAN_BUILT
        and p.get("request_plan_built") is True
        and p.get("status") == Status.PASS
        and p.get("request_budget") == REQUEST_BUDGET
        and p.get("requested_method") == ALLOWED_METHOD
    )


# --------------------------------------------------------------------------- #
# 0174UE: operator-owned credential hydration boundary
# --------------------------------------------------------------------------- #
def hydrate_telegram_credential_handle(*, operator_gate_id,
                                       operator_live_read_only_enabled=False,
                                       env_reader=None):
    """Operator-owned credential hydration boundary. Fail-closed.

    DRY-RUN DEFAULT: when live is NOT enabled, this performs NO env read at all
    and returns ``credential_not_hydrated_dry_run_only``.

    LIVE: when ``operator_live_read_only_enabled=True``, reads ONLY the one
    allowed env variable name (``CAPITAL_CHRONICLE_TELEGRAM_BOT_TOKEN``) through
    ``env_reader`` (defaults to ``os.environ.get``, imported lazily). Returns a
    REDACTED credential proof: a salted fingerprint + a bucketed length class.
    The raw token is NEVER returned, logged, or persisted. If the variable is
    missing => blocked ``credential_missing``. A suspicious token SHAPE produces
    a redacted reason only, never the value.
    """
    if not operator_gate_id:
        return _credential_result(
            CREDENTIAL_PROOF_BLOCKED, blocked=[BLOCK_OPERATOR_GATE_ID_MISSING],
            ok=False, hydrated=False, forbidden_detected=False,
            operator_gate_id=operator_gate_id, live_enabled=False,
            fingerprint=None, length_class=None)

    # DRY-RUN: explicitly do NOT read the environment.
    if not operator_live_read_only_enabled:
        return _credential_result(
            CREDENTIAL_PROOF_NOT_HYDRATED, blocked=[BLOCK_LIVE_NOT_ENABLED],
            ok=False, hydrated=False, forbidden_detected=False,
            operator_gate_id=operator_gate_id, live_enabled=False,
            fingerprint=None, length_class=None)

    # LIVE read-only: read ONLY the single allowed variable name.
    if env_reader is None:
        import os  # lazy, gated -- never read at import time
        env_reader = os.environ.get
    token = env_reader(ALLOWED_ENV_VAR)

    if not token:
        return _credential_result(
            CREDENTIAL_PROOF_BLOCKED, blocked=[BLOCK_CREDENTIAL_MISSING],
            ok=False, hydrated=False, forbidden_detected=False,
            operator_gate_id=operator_gate_id, live_enabled=True,
            fingerprint=None, length_class=None)

    # Suspicious SHAPE => redacted reason only (never echo the value).
    if _looks_suspicious(token):
        return _credential_result(
            CREDENTIAL_PROOF_BLOCKED,
            blocked=[BLOCK_CREDENTIAL_SUSPICIOUS_SHAPE], ok=False,
            hydrated=False, forbidden_detected=False,
            operator_gate_id=operator_gate_id, live_enabled=True,
            fingerprint=None, length_class=None)

    fingerprint = _credential_fingerprint(token)
    length_class = _length_class(len(token))
    # The token local goes out of scope here; only the fingerprint survives.
    return _credential_result(
        CREDENTIAL_PROOF_OK, blocked=[], ok=True, hydrated=True,
        forbidden_detected=False, operator_gate_id=operator_gate_id,
        live_enabled=True, fingerprint=fingerprint, length_class=length_class)


def _credential_result(outcome_class, *, blocked, ok, hydrated,
                       forbidden_detected, operator_gate_id, live_enabled,
                       fingerprint, length_class):
    """Build a deterministic REDACTED credential proof (pure value, no token)."""
    status = (Status.PASS if ok
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    # A stable, non-secret handle id: the bare 16-hex one-way fingerprint (or a
    # fixed placeholder). This is NOT the token and NOT reversible. A bare
    # 16-hex value is an explicitly known-safe identifier to the leak scanner.
    handle_id = fingerprint if fingerprint else "credential_not_hydrated_placeholder"
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "credential_proof_schema": CREDENTIAL_PROOF_SCHEMA,
        "credential_proof_schema_version": CREDENTIAL_PROOF_SCHEMA_VERSION,
        "status": status,
        "credential_proof_outcome_class": outcome_class,
        "credential_proof_ok": ok,
        "provider": PROVIDER_TELEGRAM,
        "operator_gate_id": operator_gate_id,
        "operator_live_read_only_enabled": live_enabled,
        "allowed_env_var_name": ALLOWED_ENV_VAR,
        "only_one_env_var_read": True,
        "env_read_performed": bool(live_enabled),
        "credential_hydrated": hydrated,
        "credential_handle_id": handle_id,
        "token_length_class": length_class,
        # Explicit "never X the token" invariants.
        "token_returned": False,
        "token_logged": False,
        "token_persisted": False,
        "reads_dotenv_file": False,
        "reads_credential_file": False,
        "scans_arbitrary_env": False,
        "blocked_reasons": sorted(set(blocked)),
        "forbidden_fields_detected": forbidden_detected,
        **_safety_flags(),
        "network_performed": False,
        "read_only_request_performed": False,
    }
    result["credential_proof_checksum"] = compute_checksum(result)
    return result


def _credential_ok(proof):
    p = proof or {}
    return (
        p.get("credential_proof_outcome_class") == CREDENTIAL_PROOF_OK
        and p.get("credential_proof_ok") is True
        and p.get("status") == Status.PASS
        and p.get("credential_hydrated") is True
    )


# --------------------------------------------------------------------------- #
# 0174UF: execute read-only identity pilot
# --------------------------------------------------------------------------- #
def _classify_provider_code(status_code):
    """Map a numeric HTTP status to a symbolic provider-code class."""
    try:
        code = int(status_code)
    except (TypeError, ValueError):
        return PROVIDER_CODE_UNKNOWN_CLASS
    if 200 <= code < 300:
        return PROVIDER_CODE_SUCCESS_CLASS
    if 400 <= code < 500:
        return PROVIDER_CODE_CLIENT_ERROR_CLASS
    if 500 <= code < 600:
        return PROVIDER_CODE_SERVER_ERROR_CLASS
    return PROVIDER_CODE_UNKNOWN_CLASS


def _default_http_transport(timeout_seconds):  # pragma: no cover - real network
    """Return a callable that performs the real, single ``getMe`` GET request.

    Imported LAZILY and built ONLY when live is enabled and no mock transport
    was injected. The token is read from the env here (again, only under the
    explicit live flag) and used ONLY to construct the URL path; it is never
    returned or stored. Returns ``(ok, status_code, payload_dict)`` and NEVER
    the raw response body or headers.
    """
    def _transport():
        import os
        import urllib.request
        import urllib.error
        token = os.environ.get(ALLOWED_ENV_VAR)
        url = ALLOWED_HOST + "/bot" + str(token) + "/" + ALLOWED_METHOD
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request,
                                        timeout=timeout_seconds) as resp:
                code = resp.getcode()
                body = json.loads(resp.read().decode("utf-8"))
                ok = bool(body.get("ok"))
                result = body.get("result") or {}
                return (ok, code, {
                    "has_id": result.get("id") is not None,
                    "has_username": bool(result.get("username")),
                })
        except urllib.error.HTTPError as exc:
            return (False, getattr(exc, "code", None), {
                "has_id": False, "has_username": False})
    return _transport


def execute_read_only_identity_pilot(request_plan, credential_proof, *,
                                     operator_live_read_only_enabled=False,
                                     http_transport=None):
    """Perform NO network unless live is explicitly enabled AND the proof is ok.

    * live False (default): returns ``identity_pilot_not_run_dry_run_only`` --
      NO network is performed.
    * live True + valid plan + ok credential proof: performs EXACTLY one
      ``getMe`` request via the injected ``http_transport`` (or the lazy default
      real transport). Provider error => redacted error proof; network exception
      => redacted blocked proof; success => redacted ok proof. NO raw body, raw
      id, raw username, raw URL, headers, or cookies are ever stored.
    """
    plan = request_plan or {}
    proof = credential_proof or {}

    if scan_for_leaks([plan, proof]):
        return build_redacted_identity_proof(
            PILOT_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE],
            request_plan=plan, forbidden_detected=True, network_performed=False)

    # DRY-RUN: no network, regardless of plan/proof contents.
    if not operator_live_read_only_enabled:
        return build_redacted_identity_proof(
            PILOT_NOT_RUN_DRY_RUN, blocked=[BLOCK_LIVE_NOT_ENABLED],
            request_plan=plan, network_performed=False)

    blocked = []
    if not _plan_built(plan):
        blocked.append(BLOCK_PLAN_NOT_BUILT)
    if not _credential_ok(proof):
        blocked.append(BLOCK_CREDENTIAL_PROOF_NOT_OK)
    if blocked:
        return build_redacted_identity_proof(
            PILOT_BLOCKED, blocked=sorted(set(blocked)), request_plan=plan,
            network_performed=False)

    timeout_seconds = plan.get("timeout_seconds", REQUEST_TIMEOUT_SECONDS)
    transport = http_transport or _default_http_transport(timeout_seconds)

    # EXACTLY one request. No retry loop, no scheduler, no polling.
    try:
        ok, status_code, redacted_fields = transport()
    except Exception:  # noqa: BLE001 - any network/systemic error fails closed
        return build_redacted_identity_proof(
            PILOT_NETWORK_BLOCKED, blocked=[], request_plan=plan,
            network_performed=True, read_only_request_performed=True,
            response_status_class=RESPONSE_STATUS_ERROR_CLASS,
            provider_code_class=PROVIDER_CODE_UNKNOWN_CLASS,
            bot_identity_present=False, bot_username_present=False,
            response_payload=None)

    fields = redacted_fields or {}
    provider_code_class = _classify_provider_code(status_code)
    if ok:
        return build_redacted_identity_proof(
            PILOT_OK, blocked=[], request_plan=plan, network_performed=True,
            read_only_request_performed=True,
            response_status_class=RESPONSE_STATUS_OK_CLASS,
            provider_code_class=provider_code_class,
            bot_identity_present=bool(fields.get("has_id")),
            bot_username_present=bool(fields.get("has_username")),
            response_payload={"ok": True})
    return build_redacted_identity_proof(
        PILOT_PROVIDER_ERROR, blocked=[], request_plan=plan,
        network_performed=True, read_only_request_performed=True,
        response_status_class=RESPONSE_STATUS_ERROR_CLASS,
        provider_code_class=provider_code_class,
        bot_identity_present=False, bot_username_present=False,
        response_payload={"ok": False})


# --------------------------------------------------------------------------- #
# 0174UG: redacted identity proof
# --------------------------------------------------------------------------- #
def build_redacted_identity_proof(outcome_class, *, blocked, request_plan,
                                  forbidden_detected=False,
                                  network_performed=False,
                                  read_only_request_performed=False,
                                  response_status_class=RESPONSE_STATUS_UNKNOWN_CLASS,
                                  provider_code_class=PROVIDER_CODE_UNKNOWN_CLASS,
                                  bot_identity_present=False,
                                  bot_username_present=False,
                                  response_payload=None):
    """Build a deterministic REDACTED identity proof. Stores NO raw response.

    Classifies ok / provider status code / bot identity + username PRESENCE
    only. Persists request + response checksums + a timestamp placeholder class.
    The raw body, raw bot id, raw username, raw URL, headers, and cookies are
    NEVER stored.
    """
    plan = request_plan or {}
    not_run = outcome_class in (PILOT_NOT_RUN_DRY_RUN,)
    ran_ok = outcome_class == PILOT_OK

    status_class = (response_status_class
                    if response_status_class in RESPONSE_STATUS_CLASSES
                    else RESPONSE_STATUS_UNKNOWN_CLASS)
    code_class = (provider_code_class
                  if provider_code_class in PROVIDER_CODE_CLASSES
                  else PROVIDER_CODE_UNKNOWN_CLASS)
    identity_class = (BOT_IDENTITY_PRESENT_CLASS if bot_identity_present
                      else BOT_IDENTITY_ABSENT_CLASS)
    username_class = (BOT_USERNAME_PRESENT_CLASS if bot_username_present
                      else BOT_USERNAME_ABSENT_CLASS)

    # Response checksum is computed over a REDACTED, presence-only summary --
    # never the raw provider body.
    if response_payload is None:
        response_checksum = None
    else:
        response_checksum = compute_checksum({
            "ok": bool(response_payload.get("ok")),
            "bot_identity_class": identity_class,
            "bot_username_class": username_class,
            "provider_code_class": code_class,
        })

    if forbidden_detected:
        status = Status.FAIL_CLOSED
    elif outcome_class in (PILOT_BLOCKED, PILOT_NETWORK_BLOCKED,
                           PILOT_NOT_RUN_DRY_RUN):
        status = Status.BLOCKED if outcome_class != PILOT_NOT_RUN_DRY_RUN \
            else Status.PASS
    elif outcome_class in (PILOT_OK, PILOT_PROVIDER_ERROR):
        status = Status.PASS
    else:
        status = Status.BLOCKED

    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "identity_proof_schema": IDENTITY_PROOF_SCHEMA,
        "identity_proof_schema_version": IDENTITY_PROOF_SCHEMA_VERSION,
        "status": status,
        "identity_proof_outcome_class": outcome_class,
        "provider": PROVIDER_TELEGRAM,
        "operator_gate_id": plan.get("operator_gate_id"),
        "identity_pilot_not_run": not_run,
        "getme_ok": ran_ok,
        "allowed_method": ALLOWED_METHOD,
        "response_status_class": status_class,
        "provider_status_code_class": code_class,
        "bot_identity_redacted_class": identity_class,
        "bot_username_redacted_class": username_class,
        "request_checksum": plan.get("request_plan_checksum"),
        "response_checksum": response_checksum,
        "timestamp_placeholder_class": TIMESTAMP_PLACEHOLDER_CLASS,
        "response_status_classes": list(RESPONSE_STATUS_CLASSES),
        "provider_status_code_classes": list(PROVIDER_CODE_CLASSES),
        "bot_identity_classes": list(BOT_IDENTITY_CLASSES),
        "bot_username_classes": list(BOT_USERNAME_CLASSES),
        # Explicit "stores no raw X" invariants.
        "stores_raw_response_body": False,
        "stores_raw_bot_id": False,
        "stores_raw_username": False,
        "stores_raw_url_with_token": False,
        "stores_headers": False,
        "stores_cookies": False,
        "stores_token": False,
        "blocked_reasons": sorted(set(blocked)),
        "forbidden_fields_detected": forbidden_detected,
        **_safety_flags(),
        # These two reflect the read-only request truth (only ever set by an
        # explicit operator-enabled live call); send/post stay False always.
        "network_performed": bool(network_performed),
        "read_only_request_performed": bool(read_only_request_performed),
        "credential_hydrated": False,
    }
    result["identity_proof_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# 0174UG: immutable identity-pilot audit packet
# --------------------------------------------------------------------------- #
def build_identity_pilot_audit_packet(request_plan, credential_proof,
                                      identity_proof, *, budget_used=0):
    """Build an immutable local audit packet. Fail-closed.

    Stores ONLY: operator gate id, credential handle id, request-plan checksum,
    redacted identity-proof checksum, and budget used. It stores NO token, NO
    raw response, NO raw URL, NO header, and NO cookie.
    """
    plan = request_plan or {}
    proof = credential_proof or {}
    identity = identity_proof or {}

    if scan_for_leaks([plan, proof, identity]):
        return _audit_result(
            AUDIT_FAIL_CLOSED, blocked=[BLOCK_FORBIDDEN_VALUE],
            forbidden_detected=True, plan=plan, proof=proof,
            identity=identity, budget_used=budget_used)

    return _audit_result(
        AUDIT_RECORDED, blocked=[], forbidden_detected=False, plan=plan,
        proof=proof, identity=identity, budget_used=budget_used)


def _audit_result(outcome_class, *, blocked, forbidden_detected, plan, proof,
                  identity, budget_used):
    """Build a deterministic immutable audit packet (pure value)."""
    status = Status.FAIL_CLOSED if forbidden_detected else Status.PASS
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "audit_schema": AUDIT_SCHEMA,
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "status": status,
        "audit_outcome_class": outcome_class,
        "provider": PROVIDER_TELEGRAM,
        "operator_gate_id": plan.get("operator_gate_id"),
        "credential_handle_id": proof.get("credential_handle_id"),
        "request_plan_checksum": plan.get("request_plan_checksum"),
        "identity_proof_checksum": identity.get("identity_proof_checksum"),
        "identity_proof_outcome_class": identity.get(
            "identity_proof_outcome_class"),
        "budget_authorized": REQUEST_BUDGET,
        "budget_used": budget_used,
        "timestamp_placeholder_class": TIMESTAMP_PLACEHOLDER_CLASS,
        # Explicit "stores no raw X" invariants.
        "stores_token": False,
        "stores_raw_response": False,
        "stores_raw_url": False,
        "stores_headers": False,
        "stores_cookies": False,
        "blocked_reasons": sorted(set(blocked)),
        "forbidden_fields_detected": forbidden_detected,
        **_safety_flags(),
        "network_performed": bool(identity.get("network_performed")),
        "read_only_request_performed": bool(
            identity.get("read_only_request_performed")),
        "credential_hydrated": False,
    }
    result["audit_checksum"] = compute_checksum(result)
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
        "request_plan_schema": REQUEST_PLAN_SCHEMA,
        "request_plan_schema_version": REQUEST_PLAN_SCHEMA_VERSION,
        "credential_proof_schema": CREDENTIAL_PROOF_SCHEMA,
        "credential_proof_schema_version": CREDENTIAL_PROOF_SCHEMA_VERSION,
        "identity_proof_schema": IDENTITY_PROOF_SCHEMA,
        "identity_proof_schema_version": IDENTITY_PROOF_SCHEMA_VERSION,
        "audit_schema": AUDIT_SCHEMA,
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "provider": PROVIDER_TELEGRAM,
        "allowed_env_var_name": ALLOWED_ENV_VAR,
        "allowed_host": ALLOWED_HOST,
        "allowed_method": ALLOWED_METHOD,
        "forbidden_methods": list(FORBIDDEN_METHODS),
        "request_budget": REQUEST_BUDGET,
        "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "default_mode": "dry_run_only",
        "live_mode_requires": "operator_live_read_only_enabled=True",
        "response_status_classes": list(RESPONSE_STATUS_CLASSES),
        "provider_status_code_classes": list(PROVIDER_CODE_CLASSES),
        "bot_identity_classes": list(BOT_IDENTITY_CLASSES),
        "bot_username_classes": list(BOT_USERNAME_CLASSES),
        "timestamp_placeholder_class": TIMESTAMP_PLACEHOLDER_CLASS,
        "request_plan_outcome_classes": [
            PLAN_BUILT, PLAN_BLOCKED, PLAN_FAIL_CLOSED],
        "credential_proof_outcome_classes": [
            CREDENTIAL_PROOF_OK, CREDENTIAL_PROOF_NOT_HYDRATED,
            CREDENTIAL_PROOF_BLOCKED, CREDENTIAL_PROOF_FAIL_CLOSED],
        "identity_proof_outcome_classes": [
            PILOT_NOT_RUN_DRY_RUN, PILOT_OK, PILOT_PROVIDER_ERROR,
            PILOT_NETWORK_BLOCKED, PILOT_BLOCKED, PILOT_FAIL_CLOSED],
        "audit_outcome_classes": [AUDIT_RECORDED, AUDIT_FAIL_CLOSED],
        "hard_invariants": [
            "first_controlled_live_read_only_step_not_posting",
            "no_sendmessage_anywhere",
            "no_posting_or_platform_write",
            "no_getupdates_or_setwebhook",
            "no_webhook_or_polling",
            "no_auto_retry",
            "no_scheduler",
            "no_autonomous_reply_or_dm",
            "only_get_me_method_allowed",
            "only_telegram_api_host_allowed",
            "request_budget_is_exactly_one",
            "explicit_short_timeout",
            "default_mode_is_dry_run_only_no_env_no_network",
            "live_requires_explicit_operator_flag",
            "reads_only_one_explicit_env_var_name",
            "no_arbitrary_env_scan",
            "no_dotenv_or_credential_file_read",
            "token_never_returned_logged_or_persisted",
            "credential_stored_as_fingerprint_and_length_class_only",
            "suspicious_token_shape_is_redacted_reason_not_value",
            "response_redacted_to_classes_and_checksums_only",
            "no_raw_response_body_bot_id_username_url_header_cookie_stored",
            "audit_stores_no_token_raw_response_url_header_cookie",
            "redaction_runs_on_every_emitted_artifact",
            "no_financial_advice_or_signal_framing",
            "missing_or_unsafe_input_blocks",
        ],
        "safety_flags": _safety_flags(),
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    """Return a deterministic, redaction-clean markdown contract document."""
    packet = build_packet()
    forbidden = ", ".join(f"`{m}`" for m in packet["forbidden_methods"])
    hard = "\n".join(f"  * `{inv}`" for inv in packet["hard_invariants"])
    return (
        f"# 0174UE/UF/UG Telegram Read-Only Identity Pilot\n\n"
        f"Task: `{TASK_LABEL}`\n\n"
        f"Model: `{MODEL}` version `{MODEL_VERSION}`\n\n"
        f"Baseline commit: `{SOURCE_BASELINE_COMMIT}`\n\n"
        f"## Role\n\n"
        f"This batch is the FIRST controlled, live-capable read-only Telegram "
        f"step. It is NOT a posting task: there is NO `sendMessage` anywhere. "
        f"The ONLY platform method recognised is the read-only identity method "
        f"`{ALLOWED_METHOD}`. By default the pilot is `dry_run_only` and "
        f"performs NO env read and NO network.\n\n"
        f"## 0174UE Request plan + credential boundary\n\n"
        f"`build_identity_pilot_request_plan(...)` validates host "
        f"(`{ALLOWED_HOST}`), method (`{ALLOWED_METHOD}` only), budget "
        f"(exactly {REQUEST_BUDGET}), and timeout "
        f"(`{REQUEST_TIMEOUT_SECONDS}`s), and blocks these forbidden methods: "
        f"{forbidden}. `hydrate_telegram_credential_handle(...)` reads ONLY the "
        f"environment variable `{ALLOWED_ENV_VAR}`, and ONLY when "
        f"`operator_live_read_only_enabled=True`. It returns a REDACTED "
        f"credential proof (fingerprint + length class); the raw token is NEVER "
        f"returned, logged, or persisted. Missing variable => blocked "
        f"`{BLOCK_CREDENTIAL_MISSING}`; suspicious shape => redacted reason "
        f"only.\n\n"
        f"## 0174UF Controlled read-only execution\n\n"
        f"`execute_read_only_identity_pilot(...)` performs NO network unless "
        f"`operator_live_read_only_enabled=True` AND the credential proof is "
        f"ok. With live disabled it returns `{PILOT_NOT_RUN_DRY_RUN}`. With "
        f"live enabled it performs EXACTLY one `{ALLOWED_METHOD}` request "
        f"through an injectable transport (a mock in tests; a lazy stdlib "
        f"`urllib` transport otherwise) -- NO retry, NO scheduler, NO webhook, "
        f"NO polling. Provider error and network exception both fail closed to "
        f"redacted proofs.\n\n"
        f"## 0174UG Redacted proof + immutable audit\n\n"
        f"`build_redacted_identity_proof(...)` classifies ok / provider status "
        f"code / bot identity + username PRESENCE only, and stores request + "
        f"response checksums + a timestamp placeholder class -- never the raw "
        f"body, raw bot id, raw username, raw URL, headers, or cookies. "
        f"`build_identity_pilot_audit_packet(...)` records the operator gate "
        f"id, credential handle id, plan checksum, identity-proof checksum, and "
        f"budget used, and stores no token / raw response / raw URL / header / "
        f"cookie.\n\n"
        f"## Hard invariants\n\n{hard}\n\n"
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
