"""Operator runner: ledger-backed, replay-guarded supervised Telegram send.

Task 0174UQ/UR/US. This drives the ACCEPTED local adapter boundary (renderer +
capability enforcer + one-request builder + redacted response shape, from
``telegram_local_adapter_contract``) AND the ACCEPTED replay guard + immutable
outcome ledger (``telegram_supervised_send_outcome_ledger``) to perform the
THIRD operator-owned supervised ``sendMessage`` -- but ONLY after a deterministic
local replay-guard preflight clears against the committed ledger AND the
operator supplies a fresh gate id.

AUTHORITY MODEL (per the master plan): the deterministic LOCAL gate is the
dispatch authority. LLMs and Telegram are NOT. The path is strictly:

    approval/evidence -> replay guard -> one request -> redacted outcome ->
    immutable ledger append.

SCOPE (tight, by design):
  * EXACTLY one ``sendMessage`` request, and ONLY if the replay guard clears.
    NO retry, NO scheduler, NO webhook, NO polling, NO ``getUpdates``, NO
    autonomous reply/DM, NO media/edit/delete, NO second send path.
  * Method ``sendMessage`` only; host ``https://api.telegram.org``; request
    budget exactly 1; timeout 10 seconds.

CREDENTIAL / DESTINATION / GATE POLICY:
  * Default no-live mode reads NO ``.env``, performs NO network, and runs only
    the deterministic preflight.
  * Live mode requires BOTH ``--from-dotenv`` AND
    ``--fresh-operator-gate <gate-id>``. It reads ONLY two local ``.env`` keys:
    ``TELEGRAM_BOT_TOKEN`` and ``TEST_TELEGRAM_CHANNEL``. No other key is read;
    ``os.environ`` is never read or mutated.
  * The raw token and raw destination are NEVER printed or persisted. The
    destination is redacted to a binding checksum/class + a presence boolean;
    the token to a one-way handle fingerprint.

Importing this module performs NO writes, NO env reads, and NO network. The
real ``sendMessage`` happens ONLY inside ``main()``/``run_ledger_guarded_send``
with live enabled, a fresh gate, a clear preflight, and no mock transport.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops import telegram_local_adapter_contract as adapter  # noqa: E402
from live_contentops import telegram_supervised_send_outcome_ledger as ledger  # noqa: E402

TASK_LABEL = (
    "TASK_CONTENTOPS_0174UQ_UR_US_TELEGRAM_LEDGER_BACKED_REPLAY_GUARDED_"
    "THIRD_SEND_GATE_BATCH_V0"
)
RUNNER_MODEL = "TELEGRAM_RUN_LEDGER_GUARDED_SUPERVISED_SEND_0174UQ_UR_US"
RUNNER_MODEL_VERSION = (
    "0174UQ_UR_US_TELEGRAM_RUN_LEDGER_GUARDED_SUPERVISED_SEND_V1"
)
EVIDENCE_SCHEMA = "contentops.telegram_ledger_guarded_supervised_send_proof_evidence"
EVIDENCE_SCHEMA_VERSION = (
    "0174UQ_UR_US_TELEGRAM_LEDGER_GUARDED_SUPERVISED_SEND_PROOF_V1"
)

REQUIRED_BASELINE_COMMIT = "7c6a75f5047a0dad368db773f1fe73fbb426bacf"

NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174UT_UU_UV_TELEGRAM_OPERATOR_SUPERVISED_SEND_LEDGER_"
    "REPLAY_CONSOLE_AND_OUTCOME_RECONCILIATION_BATCH_V0"
)

DOC_REL_DIR = "docs/automation/0174UQ_UR_US"
PACKET_FILENAME = "telegram_ledger_guarded_supervised_send_proof_packet.json"
DOC_FILENAME = "telegram_ledger_guarded_supervised_send_proof.md"

# The committed accepted ledger packet this gate loads as its prior state.
ACCEPTED_LEDGER_PACKET_REL = (
    "docs/automation/0174UN_UO_UP/"
    "telegram_supervised_send_outcome_ledger_packet.json"
)

# Optional operator-owned local credential/destination source (RUNNER only).
DOTENV_FILENAME = ".env"
DOTENV_TOKEN_KEY = "TELEGRAM_BOT_TOKEN"
DOTENV_DESTINATION_KEY = "TEST_TELEGRAM_CHANNEL"
DOTENV_ALLOWED_KEYS = (DOTENV_TOKEN_KEY, DOTENV_DESTINATION_KEY)

CREDENTIAL_SOURCE_NONE = "no_live_source"
CREDENTIAL_SOURCE_DOTENV = "operator_local_dotenv_file"
DESTINATION_SOURCE_NONE = "no_live_destination"
DESTINATION_SOURCE_DOTENV_TEST_CHANNEL = "operator_local_dotenv_test_channel"

# Deterministic, clearly non-financial-advice THIRD supervised test message.
SUPERVISED_TEST_MESSAGE = (
    "Capital Chronicle ContentOps live-gate test 3: ledger-backed "
    "replay-guarded supervised Telegram sendMessage. No market advice."
)

# Which operator-owned supervised live test this run represents (third = 3).
LIVE_TEST_SEQUENCE = 3

# Reuse the SAME fingerprint domains as the accepted 0174UK runner so the
# credential handle id + destination binding checksum match the recorded ledger
# entry exactly (this is what makes the stable payload replay key comparable).
TOKEN_HANDLE_DOMAIN = "cc_sendmessage_token_v1"
DEST_BINDING_DOMAIN = "cc_sendmessage_dest_checksum_v1"

# Symbolic outcome classes for the runner.
SEND_OK = "telegram_ledger_guarded_supervised_send_ok_redacted"
SEND_PROVIDER_ERROR = "telegram_ledger_guarded_supervised_send_provider_error_redacted"
SEND_NETWORK_BLOCKED = "telegram_ledger_guarded_supervised_send_network_blocked_redacted"
SEND_BLOCKED = "telegram_ledger_guarded_supervised_send_blocked"

# Blocked-reason classes.
BLOCK_LIVE_NOT_ENABLED = "operator_live_send_not_enabled"
BLOCK_FRESH_GATE_MISSING = "fresh_operator_gate_missing"
BLOCK_CREDENTIAL_MISSING = "credential_missing"
BLOCK_DESTINATION_MISSING = "destination_missing"
BLOCK_RENDER_NOT_OK = "rendered_payload_not_ok"
BLOCK_CAPABILITY_NOT_ALLOWED = "capability_not_allowed"
BLOCK_REQUEST_NOT_BUILT = "one_request_object_not_built"
BLOCK_REPLAY_GUARD_NOT_CLEAR = "replay_guard_not_clear"

REQUEST_BUDGET = 1
REQUEST_TIMEOUT_SECONDS = 10


# --------------------------------------------------------------------------- #
# Scanning / serialization (reuse the accepted adapter)
# --------------------------------------------------------------------------- #
def scan_evidence(packet, doc):
    """Return the combined list of redaction violations across packet + doc."""
    return adapter.scan_for_leaks(packet) + adapter.scan_for_leaks(doc)


def scan_for_financial_advice_safe(packet, doc):
    """Return the combined list of financial-advice violations across artifacts."""
    return (adapter.scan_for_financial_advice(packet)
            + adapter.scan_for_financial_advice(doc))


def _fingerprint16(value, domain):
    """Return a salted 16-hex one-way fingerprint. NEVER the raw value."""
    digest = hashlib.sha256(
        (domain + "::" + str(value)).encode("utf-8")).hexdigest()
    return digest[:16]


# --------------------------------------------------------------------------- #
# Optional operator-owned local .env credential + destination source
# --------------------------------------------------------------------------- #
def load_dotenv_values(dotenv_path):
    """Read ONLY ``TELEGRAM_BOT_TOKEN`` + ``TEST_TELEGRAM_CHANNEL`` from ``.env``.

    Reads ONLY the two allowed keys, ignores every other line (including JSON /
    service-account material and comments), strips optional surrounding quotes,
    and returns ``(token, destination)``. NEVER prints, logs, or persists either
    value, and NEVER touches ``os.environ``.
    """
    token = None
    destination = None
    path = Path(dotenv_path)
    if not path.is_file():
        return token, destination
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep != "=":
            continue
        key = key.strip()
        if key not in DOTENV_ALLOWED_KEYS:
            continue
        clean = value.strip().strip('"').strip("'").strip() or None
        if key == DOTENV_TOKEN_KEY:
            token = clean
        elif key == DOTENV_DESTINATION_KEY:
            destination = clean
    return token, destination


def _build_live_send_transport(token, destination, text, timeout_seconds):
    """Return a callable performing the single real ``sendMessage`` POST.

    Takes the token + destination explicitly so ``os.environ`` is never read or
    mutated. Returns ``(ok, status_code, {has_message_id})`` and NEVER the raw
    body, headers, cookies, or URL.
    """
    def _transport():
        import urllib.request
        import urllib.error
        url = ("https://" + adapter.TELEGRAM_API_HOST + "/bot" + str(token)
               + "/" + adapter.METHOD_SUPERVISED_SEND)
        body = json.dumps({"chat_id": str(destination), "text": text}).encode(
            "utf-8")
        request = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request,
                                        timeout=timeout_seconds) as resp:
                code = resp.getcode()
                payload = json.loads(resp.read().decode("utf-8"))
                ok = bool(payload.get("ok"))
                result = payload.get("result") or {}
                return (ok, code, {
                    "has_message_id": result.get("message_id") is not None})
        except urllib.error.HTTPError as exc:
            return (False, getattr(exc, "code", None), {
                "has_message_id": False})
    return _transport


# --------------------------------------------------------------------------- #
# Provider status-code classification (reuse adapter symbolic classes)
# --------------------------------------------------------------------------- #
def _classify_provider_code(status_code):
    try:
        code = int(status_code)
    except (TypeError, ValueError):
        return adapter.PROVIDER_CODE_UNKNOWN_CLASS
    if 200 <= code < 300:
        return adapter.PROVIDER_CODE_SUCCESS_CLASS
    if 400 <= code < 500:
        return adapter.PROVIDER_CODE_CLIENT_ERROR_CLASS
    if 500 <= code < 600:
        return adapter.PROVIDER_CODE_SERVER_ERROR_CLASS
    return adapter.PROVIDER_CODE_UNKNOWN_CLASS


# --------------------------------------------------------------------------- #
# Accepted ledger loading + candidate evidence construction
# --------------------------------------------------------------------------- #
def load_accepted_ledger(packet_path):
    """Load the committed ledger packet and return ``(entries, packet)``.

    Reconstructs the existing immutable ledger-entry list from the committed
    packet's ``current_ledger_entry`` (the accepted single recorded entry). On a
    missing/invalid packet, returns ``([], {})`` so the preflight blocks safely
    rather than silently treating a fresh send as un-guarded.
    """
    path = Path(packet_path)
    if not path.is_file():
        return [], {}
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return [], {}
    entries = []
    entry = packet.get("current_ledger_entry")
    if isinstance(entry, dict) and entry.get("ledger_entry_checksum"):
        entries.append(entry)
    return entries, packet


def build_candidate_evidence_packet(rendered, one_request, *,
                                    credential_handle_id,
                                    destination_binding_checksum,
                                    credential_source_class,
                                    destination_source_class,
                                    destination_present_redacted):
    """Build the PRE-send candidate evidence packet (no live call yet).

    Carries the redacted checksums + classes the replay guard needs:
    destination binding checksum, send text checksum, request checksum,
    credential handle id, method_name, provider, ``live_test_sequence=3``. The
    ``response_checksum`` placeholder is present (so the guard's required-field
    check is satisfied) and derived ONLY from symbolic pre-send fields; it is
    NOT a provider response (none exists yet).
    """
    request_checksum = (one_request or {}).get("one_request_checksum")
    send_text_checksum = (rendered or {}).get("send_text_checksum")
    # Deterministic, non-secret pre-send response placeholder. Never a provider
    # response; purely a symbolic "pending" marker so the candidate is a valid,
    # replay-guardable evidence shape before execution.
    response_checksum_placeholder = adapter.compute_checksum({
        "kind": "candidate_pre_send_response_placeholder",
        "send_text_checksum": send_text_checksum,
        "request_checksum": request_checksum,
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "provider": adapter.PROVIDER_TELEGRAM,
    })
    packet = {
        "task_label": TASK_LABEL,
        "provider": adapter.PROVIDER_TELEGRAM,
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "credential_handle_id": credential_handle_id,
        "credential_source_class": credential_source_class,
        "destination_source_class": destination_source_class,
        "destination_binding_checksum": destination_binding_checksum,
        "destination_present_redacted": bool(destination_present_redacted),
        "send_text_checksum": send_text_checksum,
        "request_checksum": request_checksum,
        "response_checksum": response_checksum_placeholder,
        "response_shape_checksum": None,
        "send_outcome_class": None,
        "send_succeeded": False,
        "provider_status_code_class": adapter.PROVIDER_CODE_UNKNOWN_CLASS,
        "response_status_class": adapter.RESPONSE_STATUS_UNKNOWN_CLASS,
        "redacted_message_id_class": adapter.MESSAGE_ID_ABSENT_CLASS,
        "request_budget_used": 0,
        "is_candidate_pre_send": True,
    }
    packet["evidence_checksum"] = adapter.compute_checksum(packet)
    return packet


# --------------------------------------------------------------------------- #
# Core run: preflight replay guard -> (gated) single send -> ledger append
# --------------------------------------------------------------------------- #
def run_ledger_guarded_send(*, operator_live_send_enabled=True,
                            fresh_operator_gate_id=None,
                            token=None, destination=None,
                            message_text=SUPERVISED_TEST_MESSAGE,
                            existing_ledger_entries=None,
                            http_transport=None):
    """Render + validate + replay-guard preflight, then ONE gated send + append.

    Returns a dict with the rendered payload, enforcer, one-request object, the
    candidate evidence packet, the preflight replay-guard state, the redacted
    send result, the final evidence packet, the post-send replay-guard state,
    the ledger-entry, and the append result. A live ``sendMessage`` happens ONLY
    when: live is enabled, a non-empty fresh gate is supplied, the token +
    destination are present, the local artifacts are OK, and the PREFLIGHT
    replay guard clears -- otherwise it blocks BEFORE any network call.
    """
    existing = list(existing_ledger_entries or [])
    rendered = adapter.render_telegram_payload(
        approved_text=message_text, parse_mode=adapter.PARSE_MODE_NONE)
    enforcer = adapter.enforce_capability(
        requested_capability=adapter.ALLOWED_CAPABILITY,
        requested_method=adapter.METHOD_SUPERVISED_SEND)

    token_present = bool(token)
    destination_present = bool(destination)
    fresh_gate_present = bool(fresh_operator_gate_id)
    credential_handle_id = (_fingerprint16(token, TOKEN_HANDLE_DOMAIN)
                            if token_present else None)
    destination_binding_id = (_fingerprint16(destination, "cc_sendmessage_dest_v1")
                              if destination_present else None)
    destination_binding_checksum = (
        _fingerprint16(destination, DEST_BINDING_DOMAIN)
        if destination_present else None)

    one_request = adapter.build_one_request_object(
        rendered, enforcer,
        credential_handle_id=credential_handle_id or "",
        destination_binding_id=destination_binding_id or "")

    candidate = build_candidate_evidence_packet(
        rendered, one_request,
        credential_handle_id=credential_handle_id,
        destination_binding_checksum=destination_binding_checksum,
        credential_source_class=(CREDENTIAL_SOURCE_DOTENV if token_present
                                 else CREDENTIAL_SOURCE_NONE),
        destination_source_class=(DESTINATION_SOURCE_DOTENV_TEST_CHANNEL
                                  if destination_present
                                  else DESTINATION_SOURCE_NONE),
        destination_present_redacted=destination_present)

    # Preflight replay guard against the loaded ledger using the fresh gate.
    preflight_guard = ledger.build_replay_guard_state(
        existing, candidate, operator_gate_id=fresh_operator_gate_id)

    blocked = []
    if not operator_live_send_enabled:
        blocked.append(BLOCK_LIVE_NOT_ENABLED)
    if not fresh_gate_present:
        blocked.append(BLOCK_FRESH_GATE_MISSING)
    if not token_present:
        blocked.append(BLOCK_CREDENTIAL_MISSING)
    if not destination_present:
        blocked.append(BLOCK_DESTINATION_MISSING)
    if rendered.get("rendered_payload_outcome_class") != adapter.RENDER_OK:
        blocked.append(BLOCK_RENDER_NOT_OK)
    if enforcer.get("capability_enforcer_outcome_class") != adapter.ENFORCER_ALLOWED:
        blocked.append(BLOCK_CAPABILITY_NOT_ALLOWED)
    if one_request.get("one_request_outcome_class") != adapter.REQUEST_OK:
        blocked.append(BLOCK_REQUEST_NOT_BUILT)
    if preflight_guard.get("replay_guard_outcome_class") != ledger.REPLAY_CLEAR:
        blocked.append(BLOCK_REPLAY_GUARD_NOT_CLEAR)

    if blocked:
        send_result = _blocked_send_result(sorted(set(blocked)))
    else:
        # Gated-ok: perform EXACTLY one send. No retry loop, ever.
        transport = http_transport or _build_live_send_transport(
            token, destination, message_text, REQUEST_TIMEOUT_SECONDS)
        send_result = _execute_single_send(transport)

    final_packet = _build_final_evidence(
        candidate, send_result, fresh_operator_gate_id=fresh_operator_gate_id)
    post_guard = ledger.build_replay_guard_state(
        existing, final_packet, operator_gate_id=fresh_operator_gate_id)
    entry = ledger.build_ledger_entry(
        final_packet, operator_gate_id=fresh_operator_gate_id)

    # Append ONLY if the post-send guard clears AND the send actually succeeded.
    if send_result.get("send_succeeded"):
        append = ledger.append_ledger_entry(existing, entry, post_guard)
    else:
        # Do not append a failed/blocked attempt; keep the ledger unchanged.
        append = ledger.append_ledger_entry(
            existing, entry,
            {"replay_guard_outcome_class": "not_clear",
             "replay_guard_clear": False, "status": adapter.Status.BLOCKED})

    return {
        "rendered": rendered,
        "enforcer": enforcer,
        "one_request": one_request,
        "candidate_evidence": candidate,
        "preflight_guard": preflight_guard,
        "send_result": send_result,
        "final_evidence": final_packet,
        "post_guard": post_guard,
        "ledger_entry": entry,
        "append": append,
        "fresh_operator_gate_id": fresh_operator_gate_id,
        "existing_ledger_entries": existing,
    }


def _execute_single_send(transport):
    """Perform EXACTLY one transport call; any exception fails closed (no retry)."""
    try:
        ok, status_code, redacted_fields = transport()
    except Exception:  # noqa: BLE001 - any network/systemic error fails closed
        return {
            "outcome_class": SEND_NETWORK_BLOCKED,
            "send_attempted": True,
            "send_succeeded": False,
            "budget_used": 1,
            "provider_status_code_class": adapter.PROVIDER_CODE_UNKNOWN_CLASS,
            "response_status_class": adapter.RESPONSE_STATUS_ERROR_CLASS,
            "message_id_class": adapter.MESSAGE_ID_ABSENT_CLASS,
            "blocked_reasons": [],
        }
    fields = redacted_fields or {}
    provider_code_class = _classify_provider_code(status_code)
    if ok:
        return {
            "outcome_class": SEND_OK,
            "send_attempted": True,
            "send_succeeded": True,
            "budget_used": 1,
            "provider_status_code_class": provider_code_class,
            "response_status_class": adapter.RESPONSE_STATUS_OK_CLASS,
            "message_id_class": (adapter.MESSAGE_ID_PRESENT_CLASS
                                 if fields.get("has_message_id")
                                 else adapter.MESSAGE_ID_ABSENT_CLASS),
            "blocked_reasons": [],
        }
    return {
        "outcome_class": SEND_PROVIDER_ERROR,
        "send_attempted": True,
        "send_succeeded": False,
        "budget_used": 1,
        "provider_status_code_class": provider_code_class,
        "response_status_class": adapter.RESPONSE_STATUS_ERROR_CLASS,
        "message_id_class": adapter.MESSAGE_ID_ABSENT_CLASS,
        "blocked_reasons": [],
    }


def _blocked_send_result(blocked_reasons):
    """A redacted blocked send-result with NO network performed."""
    return {
        "outcome_class": SEND_BLOCKED,
        "send_attempted": False,
        "send_succeeded": False,
        "budget_used": 0,
        "provider_status_code_class": adapter.PROVIDER_CODE_UNKNOWN_CLASS,
        "response_status_class": adapter.RESPONSE_STATUS_UNKNOWN_CLASS,
        "message_id_class": adapter.MESSAGE_ID_ABSENT_CLASS,
        "blocked_reasons": list(blocked_reasons),
    }


def compute_redacted_send_response_checksum(send_result):
    """Return a deterministic redacted response checksum, or None if no send.

    Derived ONLY from redacted symbolic fields (the R1 pattern): send outcome
    class, success boolean, provider status-code class, response status class,
    redacted message-id class, budget used, fixed ``sendMessage`` method,
    ``telegram`` provider, and the ``live_test_sequence=3`` marker. NEVER a raw
    provider response, token, raw URL, headers, cookies, raw destination, chat
    id, or username. Returns ``None`` when no send was attempted (blocked before
    network), so a blocked proof legitimately carries a null checksum.
    """
    sr = send_result or {}
    if not sr.get("send_attempted"):
        return None
    return adapter.compute_checksum({
        "send_outcome_class": sr.get("outcome_class"),
        "send_succeeded": bool(sr.get("send_succeeded")),
        "provider_status_code_class": sr.get("provider_status_code_class"),
        "response_status_class": sr.get("response_status_class"),
        "redacted_message_id_class": sr.get("message_id_class"),
        "budget_used": sr.get("budget_used"),
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "provider": adapter.PROVIDER_TELEGRAM,
        "live_test_sequence": LIVE_TEST_SEQUENCE,
    })


def _build_final_evidence(candidate, send_result, *, fresh_operator_gate_id):
    """Build the POST-send final evidence packet from the redacted outcome.

    Reuses the candidate's redacted checksums/classes and replaces the pre-send
    placeholders with the real redacted outcome + a deterministic response
    checksum + a redacted response shape. Stays a valid, replay-guardable
    evidence shape and stores NO secrets.
    """
    sr = send_result or {}
    response_checksum = compute_redacted_send_response_checksum(sr)
    response_shape = adapter.build_redacted_response_shape(
        response_status_class=sr.get("response_status_class"),
        provider_code_class=sr.get("provider_status_code_class"),
        message_id_class=sr.get("message_id_class"),
        request_checksum=candidate.get("request_checksum"),
        response_checksum=response_checksum)
    packet = {
        "task_label": TASK_LABEL,
        "provider": adapter.PROVIDER_TELEGRAM,
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "credential_handle_id": candidate.get("credential_handle_id"),
        "credential_source_class": candidate.get("credential_source_class"),
        "destination_source_class": candidate.get("destination_source_class"),
        "destination_binding_checksum": candidate.get(
            "destination_binding_checksum"),
        "destination_present_redacted": candidate.get(
            "destination_present_redacted"),
        "send_text_checksum": candidate.get("send_text_checksum"),
        "request_checksum": candidate.get("request_checksum"),
        # Real redacted outcome (or null checksum if blocked before network).
        "response_checksum": response_checksum,
        "response_shape_checksum": response_shape.get("response_shape_checksum"),
        "send_outcome_class": sr.get("outcome_class"),
        "send_succeeded": bool(sr.get("send_succeeded")),
        "provider_status_code_class": sr.get("provider_status_code_class"),
        "response_status_class": sr.get("response_status_class"),
        "redacted_message_id_class": sr.get("message_id_class"),
        "request_budget_used": sr.get("budget_used"),
        "is_candidate_pre_send": False,
    }
    # When blocked-before-network there is no response checksum; the ledger's
    # required-field check will then block the append (by design).
    if response_checksum is None:
        packet["response_checksum"] = None
    packet["evidence_checksum"] = adapter.compute_checksum(packet)
    return packet


# --------------------------------------------------------------------------- #
# Redacted proof packet + doc
# --------------------------------------------------------------------------- #
def build_proof_packet(run_result, *, accepted_ledger_packet=None,
                       start_head=None, final_head=None, origin_head=None,
                       git_status_summary=None):
    """Build the deterministic, redacted ledger-guarded send proof packet.

    Contains ONLY redacted, non-secret material: outcome/presence classes,
    checksums, replay keys, ledger manifest checksums, and boolean proofs.
    """
    accepted = accepted_ledger_packet or {}
    send_result = run_result["send_result"]
    candidate = run_result["candidate_evidence"]
    final_evidence = run_result["final_evidence"]
    post_guard = run_result["post_guard"]
    entry = run_result["ledger_entry"]
    append = run_result["append"]
    one_request = run_result["one_request"]
    rendered = run_result["rendered"]
    enforcer = run_result["enforcer"]

    previous_entry_checksum = accepted.get("current_ledger_entry_checksum")
    old_manifest = accepted.get("ledger_manifest_checksum")

    packet = {
        "task_label": TASK_LABEL,
        "model": RUNNER_MODEL,
        "model_version": RUNNER_MODEL_VERSION,
        "evidence_schema": EVIDENCE_SCHEMA,
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "status": adapter.Status.PASS,
        "provider": adapter.PROVIDER_TELEGRAM,
        # HEAD / baseline evidence.
        "required_baseline_commit": REQUIRED_BASELINE_COMMIT,
        "start_head": start_head,
        "final_head": final_head,
        "origin_head": origin_head,
        "baseline_matched": start_head == REQUIRED_BASELINE_COMMIT,
        "git_status_summary": git_status_summary,
        # Credential + destination (redacted).
        "credential_source_class": candidate.get("credential_source_class"),
        "destination_source_class": candidate.get("destination_source_class"),
        "destination_binding_checksum": candidate.get(
            "destination_binding_checksum"),
        "destination_present_redacted": candidate.get(
            "destination_present_redacted"),
        "credential_handle_id": candidate.get("credential_handle_id"),
        # Fresh operator gate.
        "fresh_operator_gate_present": bool(
            run_result.get("fresh_operator_gate_id")),
        "operator_gate_class": post_guard.get("operator_gate_class"),
        # What was attempted.
        "real_send_attempted": bool(send_result.get("send_attempted")),
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "send_outcome_class": send_result.get("outcome_class"),
        "send_succeeded": bool(send_result.get("send_succeeded")),
        "request_budget_authorized": REQUEST_BUDGET,
        "request_budget_used": send_result.get("budget_used"),
        "blocked_reasons": list(send_result.get("blocked_reasons") or []),
        # Method + host facts (symbolic; never a tokened URL).
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "api_host": adapter.TELEGRAM_API_HOST,
        "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        # Redacted provider outcome.
        "provider_status_code_class": send_result.get(
            "provider_status_code_class"),
        "response_status_class": send_result.get("response_status_class"),
        "redacted_message_id_class": send_result.get("message_id_class"),
        # Checksums.
        "rendered_payload_checksum": (rendered or {}).get(
            "rendered_payload_checksum"),
        "send_text_checksum": (rendered or {}).get("send_text_checksum"),
        "capability_enforcer_checksum": (enforcer or {}).get(
            "capability_enforcer_checksum"),
        "request_checksum": (one_request or {}).get("one_request_checksum"),
        "response_checksum": final_evidence.get("response_checksum"),
        "response_shape_checksum": final_evidence.get("response_shape_checksum"),
        "candidate_evidence_checksum": candidate.get("evidence_checksum"),
        "final_evidence_checksum": final_evidence.get("evidence_checksum"),
        # Replay guard.
        "replay_guard_outcome_class": post_guard.get(
            "replay_guard_outcome_class"),
        "preflight_replay_guard_outcome_class": run_result[
            "preflight_guard"].get("replay_guard_outcome_class"),
        "same_payload_under_fresh_gate": post_guard.get(
            "same_payload_under_fresh_gate"),
        "exact_run_replay_key": post_guard.get("exact_run_replay_key"),
        "stable_payload_replay_key": post_guard.get("stable_payload_replay_key"),
        # Ledger append.
        "previous_ledger_entry_checksum": previous_entry_checksum,
        "new_ledger_entry_checksum": entry.get("ledger_entry_checksum"),
        "ledger_entry_checksum": entry.get("ledger_entry_checksum"),
        "old_ledger_manifest_checksum": old_manifest,
        "new_ledger_manifest_checksum": append.get("ledger_manifest_checksum"),
        "ledger_manifest_checksum": append.get("ledger_manifest_checksum"),
        "ledger_entry_count": append.get("ledger_entry_count"),
        "appended": bool(append.get("appended")),
        "append_status_class": append.get("append_status_class"),
        "input_ledger_unchanged": append.get("input_ledger_unchanged"),
        # No-secret proofs.
        "stores_no_token": True,
        "stores_no_raw_destination": True,
        "stores_no_raw_response": True,
        "stores_no_raw_url": True,
        "stores_no_headers": True,
        "stores_no_cookies": True,
        "stores_no_raw_chat_id": True,
        "stores_no_username": True,
        # No-extra-behavior proofs.
        "no_retry": True,
        "no_scheduler": True,
        "no_webhook": True,
        "no_polling": True,
        "no_get_updates": True,
        "no_autonomous_reply": True,
        "no_media_edit_delete": True,
        "no_second_send_path": True,
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
    }
    packet["evidence_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_proof_doc(packet):
    """Render a deterministic, scanner-safe markdown proof document."""
    attempted = "yes" if packet["real_send_attempted"] else "no"
    succeeded = "yes" if packet["send_succeeded"] else "no"
    appended = "yes" if packet["appended"] else "no"
    return (
        "# 0174UQ/UR/US Telegram Ledger-Backed Replay-Guarded Supervised Send "
        "Proof\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Run summary\n\n"
        f"- Required baseline: `{packet['required_baseline_commit']}`\n"
        f"- Start HEAD: `{packet['start_head']}`\n"
        f"- Final HEAD: `{packet['final_head']}`\n"
        f"- Origin HEAD: `{packet['origin_head']}`\n"
        f"- Baseline matched: `{packet['baseline_matched']}`\n"
        f"- Credential source: `{packet['credential_source_class']}`\n"
        f"- Destination source: `{packet['destination_source_class']}`\n"
        f"- Destination binding checksum: "
        f"`{packet['destination_binding_checksum']}`\n"
        f"- Fresh operator gate present: "
        f"`{packet['fresh_operator_gate_present']}`\n"
        f"- Real sendMessage attempted: `{attempted}`\n"
        f"- Real sendMessage succeeded: `{succeeded}`\n"
        f"- Live test sequence: `{packet['live_test_sequence']}` "
        "(third supervised live test)\n"
        f"- Send outcome class: `{packet['send_outcome_class']}`\n"
        f"- Request budget used: `{packet['request_budget_used']}` of "
        f"`{packet['request_budget_authorized']}`\n\n"
        "## Replay guard\n\n"
        f"- Preflight outcome: "
        f"`{packet['preflight_replay_guard_outcome_class']}`\n"
        f"- Post-send outcome: `{packet['replay_guard_outcome_class']}`\n"
        f"- Same payload under fresh gate: "
        f"`{packet['same_payload_under_fresh_gate']}`\n"
        f"- Exact run replay key: `{packet['exact_run_replay_key']}`\n"
        f"- Stable payload replay key: "
        f"`{packet['stable_payload_replay_key']}`\n\n"
        "## Redacted provider outcome\n\n"
        f"- Provider status code class: `{packet['provider_status_code_class']}`\n"
        f"- Response status class: `{packet['response_status_class']}`\n"
        f"- Redacted message id class: `{packet['redacted_message_id_class']}`\n\n"
        "## Checksums + ledger\n\n"
        f"- Request checksum: `{packet['request_checksum']}`\n"
        f"- Response checksum: `{packet['response_checksum']}`\n"
        f"- Response shape checksum: `{packet['response_shape_checksum']}`\n"
        f"- Previous ledger entry checksum: "
        f"`{packet['previous_ledger_entry_checksum']}`\n"
        f"- New ledger entry checksum: `{packet['new_ledger_entry_checksum']}`\n"
        f"- Old ledger manifest checksum: "
        f"`{packet['old_ledger_manifest_checksum']}`\n"
        f"- New ledger manifest checksum: "
        f"`{packet['new_ledger_manifest_checksum']}`\n"
        f"- Ledger entry count: `{packet['ledger_entry_count']}`\n"
        f"- Appended: `{appended}`\n"
        f"- Evidence checksum: `{packet['evidence_checksum']}`\n\n"
        "## Safety proofs\n\n"
        f"- Stores no token: `{packet['stores_no_token']}`\n"
        f"- Stores no raw destination: `{packet['stores_no_raw_destination']}`\n"
        f"- Stores no raw response: `{packet['stores_no_raw_response']}`\n"
        f"- Stores no raw URL: `{packet['stores_no_raw_url']}`\n"
        f"- Stores no headers: `{packet['stores_no_headers']}`\n"
        f"- Stores no cookies: `{packet['stores_no_cookies']}`\n"
        f"- Stores no raw chat id: `{packet['stores_no_raw_chat_id']}`\n"
        f"- No retry: `{packet['no_retry']}`\n"
        f"- No scheduler: `{packet['no_scheduler']}`\n"
        f"- No webhook: `{packet['no_webhook']}`\n"
        f"- No polling: `{packet['no_polling']}`\n"
        f"- No getUpdates: `{packet['no_get_updates']}`\n"
        f"- No autonomous reply: `{packet['no_autonomous_reply']}`\n"
        f"- No media/edit/delete: `{packet['no_media_edit_delete']}`\n"
        f"- No second send path: `{packet['no_second_send_path']}`\n\n"
        f"## Next recommended task\n\n`{packet['next_recommended_task']}`\n")


def write_evidence(base_dir, packet, doc):
    """Write the proof packet + doc under ``base_dir`` ONLY if scanner-clean.

    Returns the list of written absolute paths. Raises ``RuntimeError`` if either
    the redaction scanner or the financial-advice scanner flags anything, so
    unsafe evidence is never persisted.
    """
    violations = scan_evidence(packet, doc) + scan_for_financial_advice_safe(
        packet, doc)
    if violations:
        raise RuntimeError(
            "refusing to write evidence: scan found %d violation(s)"
            % len(violations))
    out_dir = Path(base_dir) / DOC_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / PACKET_FILENAME
    doc_path = out_dir / DOC_FILENAME
    packet_path.write_text(adapter.serialize(packet), encoding="utf-8",
                           newline="\n")
    doc_path.write_text(doc, encoding="utf-8", newline="\n")
    return [str(packet_path), str(doc_path)]


# --------------------------------------------------------------------------- #
# Git helpers (read-only; used only by main())
# --------------------------------------------------------------------------- #
def _git(*args):
    return subprocess.run(["git", *args], cwd=str(ROOT),
                          capture_output=True, text=True)


def _head(ref="HEAD"):
    res = _git("rev-parse", ref)
    return res.stdout.strip() if res.returncode == 0 else None


def _git_status_summary():
    """A compact, non-secret summary: counts only, never file contents."""
    res = _git("status", "--porcelain")
    if res.returncode != 0:
        return "git_status_unavailable"
    lines = [ln for ln in res.stdout.splitlines() if ln.strip()]
    return "changed_entries=%d" % len(lines)


def _parse_fresh_gate(argv):
    """Return the ``--fresh-operator-gate`` value, or None if absent/empty."""
    flag = "--fresh-operator-gate"
    if flag not in argv:
        return None
    idx = argv.index(flag)
    if idx + 1 >= len(argv):
        return None
    value = str(argv[idx + 1]).strip()
    # Deterministic-safe: a bare non-empty token without whitespace.
    if not value or value.startswith("--"):
        return None
    return value


def main(argv=None):
    """Run the operator-owned ledger-backed replay-guarded supervised send.

    Default no-live mode reads no ``.env``, performs no network, and runs only
    the deterministic preflight. With BOTH ``--from-dotenv`` AND
    ``--fresh-operator-gate <id>`` the runner reads ONLY the token + test
    destination, evaluates the replay guard against the committed ledger, and
    performs EXACTLY one supervised ``sendMessage`` ONLY if the guard clears. The
    token and raw destination are never printed or persisted.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    use_dotenv = "--from-dotenv" in argv
    fresh_gate_id = _parse_fresh_gate(argv)
    start_head = _head("HEAD")

    accepted_entries, accepted_packet = load_accepted_ledger(
        Path(ROOT) / ACCEPTED_LEDGER_PACKET_REL)

    if use_dotenv:
        token, destination = load_dotenv_values(Path(ROOT) / DOTENV_FILENAME)
        live_enabled = True
    else:
        token, destination = None, None
        live_enabled = False

    run_result = run_ledger_guarded_send(
        operator_live_send_enabled=live_enabled,
        fresh_operator_gate_id=fresh_gate_id,
        token=token, destination=destination,
        existing_ledger_entries=accepted_entries)

    # Drop sensitive locals promptly; never stored.
    del token, destination

    final_head = _head("HEAD")
    origin_head = _head("origin/master")
    status_summary = _git_status_summary()

    packet = build_proof_packet(
        run_result, accepted_ledger_packet=accepted_packet,
        start_head=start_head, final_head=final_head, origin_head=origin_head,
        git_status_summary=status_summary)
    doc = build_proof_doc(packet)
    written = write_evidence(ROOT, packet, doc)

    # Console output is redacted: only outcome classes + booleans.
    print("TASK " + TASK_LABEL)
    print("REAL_SENDMESSAGE_ATTEMPTED " + str(packet["real_send_attempted"]))
    print("REAL_SENDMESSAGE_SUCCEEDED " + str(packet["send_succeeded"]))
    print("REPLAY_GUARD_OUTCOME " + str(packet["replay_guard_outcome_class"]))
    print("SAME_PAYLOAD_UNDER_FRESH_GATE "
          + str(packet["same_payload_under_fresh_gate"]))
    print("FRESH_GATE_PRESENT " + str(packet["fresh_operator_gate_present"]))
    print("SEND_OUTCOME " + str(packet["send_outcome_class"]))
    print("BUDGET_USED " + str(packet["request_budget_used"]))
    print("APPENDED " + str(packet["appended"]))
    print("LEDGER_ENTRY_COUNT " + str(packet["ledger_entry_count"]))
    print("NEW_LEDGER_MANIFEST " + str(packet["new_ledger_manifest_checksum"]))
    print("EVIDENCE_SCAN_CLEAN")
    for path in written:
        print("WROTE " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
