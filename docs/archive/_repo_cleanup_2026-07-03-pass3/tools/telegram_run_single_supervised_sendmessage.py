"""Operator runner for the FIRST single supervised Telegram ``sendMessage``.

Task 0174UK/UL/UM. This drives the ALREADY-ACCEPTED
``live_contentops.telegram_local_adapter_contract`` boundary (renderer +
capability enforcer + one-request builder + redacted response shape) to perform
EXACTLY one real, operator-owned, supervised ``sendMessage`` to the
operator-controlled TEST destination -- and ONLY when the operator explicitly
passes ``--from-dotenv`` and both the token and the test destination are present.

SCOPE (tight, by design):
  * EXACTLY one ``sendMessage`` request. NO retry, NO scheduler, NO webhook, NO
    polling, NO ``getUpdates``, NO autonomous reply/DM, NO media/edit/delete, and
    NO second send after a provider error.
  * Method ``sendMessage`` only; host ``https://api.telegram.org``; request
    budget exactly 1; timeout 10 seconds.

CREDENTIAL / DESTINATION POLICY (runner-side, never a library import-time read):
  * Default no-live mode reads NO ``.env`` and performs NO network.
  * Live mode requires explicit ``--from-dotenv`` and reads ONLY two local
    ``.env`` keys: ``TELEGRAM_BOT_TOKEN`` and ``TEST_TELEGRAM_CHANNEL``. No other
    key is read; ``os.environ`` is never read or mutated.
  * The raw token and the raw destination are NEVER printed or persisted. The
    destination is redacted to a binding checksum/class + a presence boolean
    only; the token to a one-way handle fingerprint only.

EVIDENCE: only scanner-clean redacted material is written -- no token, no raw
response, no raw URL, no headers, no cookies, no raw chat/channel id, no raw
username, no unredacted provider body, no second-send path, no
scheduler/retry/webhook/polling.

Importing this module performs NO writes, NO env reads, and NO network. The real
``sendMessage`` happens ONLY inside ``main()`` with ``--from-dotenv`` (or an
explicit ``run_single_supervised_send`` call with live enabled and no mock
transport).
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

TASK_LABEL = (
    "TASK_CONTENTOPS_0174UK_UL_UM_TELEGRAM_OPERATOR_OWNED_SINGLE_SUPERVISED_"
    "SENDMESSAGE_LIVE_GATE_BATCH_V0"
)
RUNNER_MODEL = "TELEGRAM_RUN_SINGLE_SUPERVISED_SENDMESSAGE_0174UK_UL_UM"
RUNNER_MODEL_VERSION = "0174UK_UL_UM_TELEGRAM_RUN_SINGLE_SUPERVISED_SENDMESSAGE_V1"
EVIDENCE_SCHEMA = "contentops.telegram_single_supervised_sendmessage_proof_evidence"
EVIDENCE_SCHEMA_VERSION = (
    "0174UK_UL_UM_TELEGRAM_SINGLE_SUPERVISED_SENDMESSAGE_PROOF_V1"
)

REQUIRED_BASELINE_COMMIT = "001fd2feb9edaa78348a48b592114e35cadf1a88"
OPERATOR_GATE_ID = "operator_run_0174uk_ul_um_single_supervised_sendmessage"

NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174UN_UO_UP_TELEGRAM_OPERATOR_SUPERVISED_SEND_"
    "OUTCOME_LEDGER_AND_REPLAY_GUARD_BATCH_V0"
)

DOC_REL_DIR = "docs/automation/0174UK_UL_UM"
PACKET_FILENAME = "telegram_single_supervised_sendmessage_proof_packet.json"
DOC_FILENAME = "telegram_single_supervised_sendmessage_proof.md"

# Optional operator-owned local credential/destination source (RUNNER only).
DOTENV_FILENAME = ".env"
DOTENV_TOKEN_KEY = "TELEGRAM_BOT_TOKEN"
DOTENV_DESTINATION_KEY = "TEST_TELEGRAM_CHANNEL"
DOTENV_ALLOWED_KEYS = (DOTENV_TOKEN_KEY, DOTENV_DESTINATION_KEY)

CREDENTIAL_SOURCE_NONE = "no_live_source"
CREDENTIAL_SOURCE_DOTENV = "operator_local_dotenv_file"
DESTINATION_SOURCE_NONE = "no_live_destination"
DESTINATION_SOURCE_DOTENV_TEST_CHANNEL = "operator_local_dotenv_test_channel"

# Deterministic, clearly non-financial-advice supervised test message. This R1
# patch runs the SECOND operator-owned supervised live send.
SUPERVISED_TEST_MESSAGE = (
    "Capital Chronicle ContentOps live-gate test 2: supervised single Telegram "
    "sendMessage verification. No market advice."
)

# Which operator-owned supervised live test this run represents (R1 = 2).
LIVE_TEST_SEQUENCE = 2

# Symbolic outcome classes for the runner.
SEND_OK = "telegram_single_supervised_sendmessage_ok_redacted"
SEND_PROVIDER_ERROR = "telegram_single_supervised_sendmessage_provider_error_redacted"
SEND_NETWORK_BLOCKED = "telegram_single_supervised_sendmessage_network_blocked_redacted"
SEND_BLOCKED = "telegram_single_supervised_sendmessage_blocked"

# Blocked-reason classes.
BLOCK_LIVE_NOT_ENABLED = "operator_live_send_not_enabled"
BLOCK_CREDENTIAL_MISSING = "credential_missing"
BLOCK_DESTINATION_MISSING = "destination_missing"
BLOCK_RENDER_NOT_OK = "rendered_payload_not_ok"
BLOCK_CAPABILITY_NOT_ALLOWED = "capability_not_allowed"
BLOCK_REQUEST_NOT_BUILT = "one_request_object_not_built"

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
    """Return a salted 16-hex one-way fingerprint. NEVER the raw value.

    A bare 16-hex value is an explicitly known-safe identifier to the leak
    scanner, so it is safe to persist as a binding/handle id.
    """
    digest = hashlib.sha256(
        (domain + "::" + str(value)).encode("utf-8")).hexdigest()
    return digest[:16]


# --------------------------------------------------------------------------- #
# Optional operator-owned local .env credential + destination source
# --------------------------------------------------------------------------- #
def load_dotenv_values(dotenv_path):
    """Read ONLY ``TELEGRAM_BOT_TOKEN`` + ``TEST_TELEGRAM_CHANNEL`` from ``.env``.

    Runner-side convenience for IDE/sandbox use where the shell environment can
    not be set. Reads ONLY the two allowed keys, ignores every other line
    (including any JSON/service-account material and comments), strips optional
    surrounding quotes, and returns ``(token, destination)`` where each is the
    string value or ``None``. NEVER prints, logs, or persists either value.
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
# Core run: render -> enforce -> build one-request -> (gated) single send
# --------------------------------------------------------------------------- #
def run_single_supervised_send(*, operator_live_send_enabled=True,
                               token=None, destination=None,
                               message_text=SUPERVISED_TEST_MESSAGE,
                               http_transport=None):
    """Render + validate, then perform EXACTLY one supervised send if gated-ok.

    Returns ``(rendered, enforcer, one_request, send_result)`` where
    ``send_result`` is a redacted dict describing the (attempted) send. With
    ``operator_live_send_enabled=False`` no network occurs (a blocked result is
    returned). Missing token or destination blocks BEFORE any network call. The
    rendered payload + capability + one-request object are reused from the
    accepted adapter so the request is bound to exactly one authorized send.
    """
    rendered = adapter.render_telegram_payload(
        approved_text=message_text, parse_mode=adapter.PARSE_MODE_NONE)
    enforcer = adapter.enforce_capability(
        requested_capability=adapter.ALLOWED_CAPABILITY,
        requested_method=adapter.METHOD_SUPERVISED_SEND)

    token_present = bool(token)
    destination_present = bool(destination)
    credential_handle_id = (_fingerprint16(token, "cc_sendmessage_token_v1")
                            if token_present else None)
    destination_binding_id = (
        _fingerprint16(destination, "cc_sendmessage_dest_v1")
        if destination_present else None)

    one_request = adapter.build_one_request_object(
        rendered, enforcer,
        credential_handle_id=credential_handle_id or "",
        destination_binding_id=destination_binding_id or "")

    blocked = []
    if not operator_live_send_enabled:
        blocked.append(BLOCK_LIVE_NOT_ENABLED)
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

    if blocked:
        return rendered, enforcer, one_request, _blocked_send_result(
            sorted(set(blocked)))

    # Gated-ok: perform EXACTLY one send. No retry loop, ever.
    transport = http_transport or _build_live_send_transport(
        token, destination, message_text, REQUEST_TIMEOUT_SECONDS)
    try:
        ok, status_code, redacted_fields = transport()
    except Exception:  # noqa: BLE001 - any network/systemic error fails closed
        return rendered, enforcer, one_request, {
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
        return rendered, enforcer, one_request, {
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
    return rendered, enforcer, one_request, {
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

    The checksum is derived ONLY from redacted symbolic fields -- the send
    outcome class, the success boolean, the provider status-code class, the
    response status class, the redacted message-id class, the budget used, plus
    the fixed ``sendMessage`` method name, the ``telegram`` provider, and the
    ``live_test_sequence`` marker. It NEVER incorporates a raw provider
    response, token, raw URL, headers, cookies, raw destination, chat id, or
    username.

    Returns ``None`` when no send was attempted (e.g. blocked before network),
    so a blocked proof legitimately carries a null ``response_checksum``; any
    attempted send (success, provider error, or network exception) yields a
    non-null, deterministic checksum.
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


# --------------------------------------------------------------------------- #
# Redacted evidence packet + doc
# --------------------------------------------------------------------------- #
def build_evidence_packet(rendered, enforcer, one_request, send_result, *,
                          start_head=None, final_head=None, origin_head=None,
                          git_status_summary=None,
                          credential_source_class=CREDENTIAL_SOURCE_NONE,
                          destination_source_class=DESTINATION_SOURCE_NONE,
                          destination_binding_checksum=None,
                          destination_present_redacted=False,
                          real_send_attempted=False):
    """Build the deterministic, redacted evidence packet (pure value).

    Contains ONLY redacted, non-secret material: outcome classes, presence
    classes, checksums, and boolean proofs. NO token, NO raw destination, NO raw
    response, NO raw URL, NO header, NO cookie.
    """
    request_descriptor = (one_request or {}).get("request_descriptor") or {}
    response_checksum = compute_redacted_send_response_checksum(send_result)
    response_shape = adapter.build_redacted_response_shape(
        response_status_class=send_result.get("response_status_class"),
        provider_code_class=send_result.get("provider_status_code_class"),
        message_id_class=send_result.get("message_id_class"),
        request_checksum=(one_request or {}).get("one_request_checksum"),
        response_checksum=response_checksum)

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
        "credential_source_class": credential_source_class,
        "destination_source_class": destination_source_class,
        "destination_binding_checksum": destination_binding_checksum,
        "destination_binding_id": (one_request or {}).get(
            "destination_binding_id"),
        "destination_present_redacted": bool(destination_present_redacted),
        "credential_handle_id": (one_request or {}).get("credential_handle_id"),
        # What was attempted.
        "real_send_attempted": bool(real_send_attempted),
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "send_outcome_class": send_result.get("outcome_class"),
        "send_attempted": bool(send_result.get("send_attempted")),
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
        "response_checksum": response_shape.get("response_checksum"),
        "response_shape_checksum": response_shape.get("response_shape_checksum"),
        # Redacted-payload facts (from the accepted one-request object).
        "send_text_length": (rendered or {}).get("send_text_length"),
        "request_count_authorized": request_descriptor.get(
            "request_count_authorized"),
        "request_contains_url_with_token": request_descriptor.get(
            "contains_url_with_token"),
        "request_contains_token_value": request_descriptor.get(
            "contains_token_value"),
        "request_contains_raw_chat_id": request_descriptor.get(
            "contains_raw_chat_id"),
        # No-secret proofs.
        "stores_no_token": True,
        "stores_no_raw_destination": True,
        "stores_no_raw_response": response_shape.get(
            "stores_raw_provider_response") is False,
        "stores_no_raw_url": response_shape.get("stores_raw_url") is False,
        "stores_no_headers": response_shape.get("stores_headers") is False,
        "stores_no_cookies": response_shape.get("stores_cookies") is False,
        "stores_no_raw_chat_id": response_shape.get(
            "stores_raw_chat_id") is False,
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


def build_evidence_doc(packet):
    """Render a deterministic, scanner-safe markdown evidence document."""
    attempted = "yes" if packet["real_send_attempted"] else "no"
    succeeded = "yes" if packet["send_succeeded"] else "no"
    present = "yes" if packet["destination_present_redacted"] else "no"
    return (
        f"# 0174UK/UL/UM Telegram Single Supervised sendMessage Proof\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        f"## Run summary\n\n"
        f"- Required baseline: `{packet['required_baseline_commit']}`\n"
        f"- Start HEAD: `{packet['start_head']}`\n"
        f"- Final HEAD: `{packet['final_head']}`\n"
        f"- Origin HEAD: `{packet['origin_head']}`\n"
        f"- Baseline matched: `{packet['baseline_matched']}`\n"
        f"- Credential source: `{packet['credential_source_class']}`\n"
        f"- Destination source: `{packet['destination_source_class']}`\n"
        f"- Destination binding checksum: "
        f"`{packet['destination_binding_checksum']}`\n"
        f"- Destination present (redacted): `{present}`\n"
        f"- Real sendMessage attempted: `{attempted}`\n"
        f"- Real sendMessage succeeded: `{succeeded}`\n"
        f"- Live test sequence: `{packet['live_test_sequence']}` "
        f"(second supervised live test)\n"
        f"- Send outcome class: `{packet['send_outcome_class']}`\n"
        f"- Request budget used: `{packet['request_budget_used']}` of "
        f"`{packet['request_budget_authorized']}`\n\n"
        f"## Redacted provider outcome\n\n"
        f"- Provider status code class: `{packet['provider_status_code_class']}`\n"
        f"- Response status class: `{packet['response_status_class']}`\n"
        f"- Redacted message id class: `{packet['redacted_message_id_class']}`\n\n"
        f"## Checksums\n\n"
        f"- Rendered payload checksum: `{packet['rendered_payload_checksum']}`\n"
        f"- Send text checksum: `{packet['send_text_checksum']}`\n"
        f"- Capability enforcer checksum: "
        f"`{packet['capability_enforcer_checksum']}`\n"
        f"- Request checksum: `{packet['request_checksum']}`\n"
        f"- Response checksum: `{packet['response_checksum']}`\n"
        f"- Evidence checksum: `{packet['evidence_checksum']}`\n\n"
        f"## Safety proofs\n\n"
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
    """Write the evidence packet + doc under ``base_dir`` ONLY if scanner-clean.

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


def main(argv=None):
    """Perform the real operator-owned single supervised sendMessage run.

    Default no-live mode reads no ``.env`` and performs no network. With
    ``--from-dotenv`` the runner reads ONLY the token + test destination from the
    local ``.env`` and performs EXACTLY one supervised ``sendMessage``. The token
    and raw destination are never printed or persisted.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    use_dotenv = "--from-dotenv" in argv
    start_head = _head("HEAD")

    if use_dotenv:
        token, destination = load_dotenv_values(Path(ROOT) / DOTENV_FILENAME)
        credential_source_class = CREDENTIAL_SOURCE_DOTENV
        destination_source_class = DESTINATION_SOURCE_DOTENV_TEST_CHANNEL
        live_enabled = True
    else:
        token, destination = None, None
        credential_source_class = CREDENTIAL_SOURCE_NONE
        destination_source_class = DESTINATION_SOURCE_NONE
        live_enabled = False

    destination_present = bool(destination)
    destination_binding_checksum = (
        _fingerprint16(destination, "cc_sendmessage_dest_checksum_v1")
        if destination_present else None)

    rendered, enforcer, one_request, send_result = run_single_supervised_send(
        operator_live_send_enabled=live_enabled,
        token=token, destination=destination)

    # Drop sensitive locals promptly; never stored.
    del token, destination

    final_head = _head("HEAD")
    origin_head = _head("origin/master")
    status_summary = _git_status_summary()

    packet = build_evidence_packet(
        rendered, enforcer, one_request, send_result,
        start_head=start_head, final_head=final_head, origin_head=origin_head,
        git_status_summary=status_summary,
        credential_source_class=credential_source_class,
        destination_source_class=destination_source_class,
        destination_binding_checksum=destination_binding_checksum,
        destination_present_redacted=destination_present,
        real_send_attempted=bool(send_result.get("send_attempted")))
    doc = build_evidence_doc(packet)

    written = write_evidence(ROOT, packet, doc)

    # Console output is redacted: only outcome classes + booleans, never the
    # token, raw destination, or raw provider response.
    print("TASK " + TASK_LABEL)
    print("REAL_SENDMESSAGE_ATTEMPTED " + str(packet["real_send_attempted"]))
    print("REAL_SENDMESSAGE_SUCCEEDED " + str(packet["send_succeeded"]))
    print("CREDENTIAL_SOURCE " + str(packet["credential_source_class"]))
    print("DESTINATION_SOURCE " + str(packet["destination_source_class"]))
    print("DESTINATION_PRESENT_REDACTED "
          + str(packet["destination_present_redacted"]))
    print("SEND_OUTCOME " + str(packet["send_outcome_class"]))
    print("PROVIDER_CODE_CLASS " + str(packet["provider_status_code_class"]))
    print("RESPONSE_STATUS_CLASS " + str(packet["response_status_class"]))
    print("MESSAGE_ID_CLASS " + str(packet["redacted_message_id_class"]))
    print("BUDGET_USED " + str(packet["request_budget_used"]))
    print("EVIDENCE_SCAN_CLEAN")
    for path in written:
        print("WROTE " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
