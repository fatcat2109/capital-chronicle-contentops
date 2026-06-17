"""Operator runner for the FIRST real Telegram read-only ``getMe`` identity proof.

Task 0174UH/UI/UJ. This drives the ALREADY-ACCEPTED
``live_contentops.telegram_read_only_identity_pilot`` boundary to perform EXACTLY
one real, operator-owned, read-only ``getMe`` identity proof -- and ONLY when the
operator explicitly enables it and the credential env var is present.

This is NOT a posting task. There is NO ``sendMessage``, NO ``getUpdates``, NO
``setWebhook``, NO retry, NO scheduler, NO webhook, NO polling anywhere.

CREDENTIAL POLICY (delegated entirely to the accepted pilot boundary):
  * reads ONLY ``CAPITAL_CHRONICLE_TELEGRAM_BOT_TOKEN`` from the OS environment,
    and ONLY when ``operator_live_read_only_enabled=True``;
  * NEVER reads ``.env`` / credential files / keyring / browser session / any
    other env var;
  * NEVER prints, logs, returns, or persists the raw token;
  * NEVER prints or persists the raw provider response, raw URL, headers, or
    cookies.

The runner itself never touches ``os.environ`` for the token: it passes
``env_reader=None`` so the accepted pilot performs the single gated read through
its own lazy seam. In tests an injected mock ``env_reader`` and mock
``http_transport`` are used, so NO real network call and NO real env read occur.

Importing this module performs NO writes, NO env reads, and NO network. The real
``getMe`` happens ONLY inside ``main()`` (or an explicit ``run_identity_proof``
call with live enabled and no mock transport).
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops import telegram_read_only_identity_pilot as pilot  # noqa: E402

TASK_LABEL = (
    "TASK_CONTENTOPS_0174UH_UI_UJ_TELEGRAM_OPERATOR_RUN_REAL_GETME_PROOF_BATCH_V0"
)
RUNNER_MODEL = "TELEGRAM_RUN_READ_ONLY_IDENTITY_PILOT_0174UH_UI_UJ"
RUNNER_MODEL_VERSION = "0174UH_UI_UJ_TELEGRAM_RUN_READ_ONLY_IDENTITY_PILOT_V1"
EVIDENCE_SCHEMA = "contentops.telegram_real_getme_identity_proof_evidence"
EVIDENCE_SCHEMA_VERSION = "0174UH_UI_UJ_TELEGRAM_REAL_GETME_IDENTITY_PROOF_V1"

REQUIRED_BASELINE_COMMIT = "42eff73170d847a7ace2b61ebe8e4d92da96149e"
OPERATOR_GATE_ID = "operator_run_0174uh_ui_uj_real_getme_identity_proof"

NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174UK_UL_UM_TELEGRAM_OPERATOR_OWNED_SINGLE_SUPERVISED_"
    "SENDMESSAGE_LIVE_GATE_BATCH_V0"
)

DOC_REL_DIR = "docs/automation/0174UH_UI_UJ"
PACKET_FILENAME = "telegram_real_getme_identity_proof_packet.json"
DOC_FILENAME = "telegram_real_getme_identity_proof.md"


# --------------------------------------------------------------------------- #
# Core run (delegates entirely to the accepted pilot boundary)
# --------------------------------------------------------------------------- #
def run_identity_proof(*, operator_live_read_only_enabled=True,
                       operator_gate_id=OPERATOR_GATE_ID,
                       env_reader=None, http_transport=None):
    """Drive plan -> hydrate -> execute -> audit. Returns the four artifacts.

    With ``operator_live_read_only_enabled=False`` this is a pure dry-run: the
    pilot performs NO env read and NO network. With live enabled and no injected
    transport, the pilot performs EXACTLY one real ``getMe`` (and a single gated
    env read of the one allowed variable). Missing credential or a failed request
    still yields a redacted, blocked identity proof -- never a retry.
    """
    plan = pilot.build_identity_pilot_request_plan(
        operator_gate_id=operator_gate_id,
        operator_live_read_only_enabled=operator_live_read_only_enabled,
        requested_method=pilot.ALLOWED_METHOD,
        requested_host=pilot.ALLOWED_HOST,
        request_budget=pilot.REQUEST_BUDGET,
        timeout_seconds=pilot.REQUEST_TIMEOUT_SECONDS,
        auto_retry=False, scheduler=False, webhook=False, polling=False)

    proof = pilot.hydrate_telegram_credential_handle(
        operator_gate_id=operator_gate_id,
        operator_live_read_only_enabled=operator_live_read_only_enabled,
        env_reader=env_reader)

    identity = pilot.execute_read_only_identity_pilot(
        plan, proof,
        operator_live_read_only_enabled=operator_live_read_only_enabled,
        http_transport=http_transport)

    budget_used = 1 if identity.get("read_only_request_performed") else 0
    audit = pilot.build_identity_pilot_audit_packet(
        plan, proof, identity, budget_used=budget_used)

    return plan, proof, identity, audit


# --------------------------------------------------------------------------- #
# Redacted evidence packet + doc
# --------------------------------------------------------------------------- #
def build_evidence_packet(plan, proof, identity, audit, *,
                          start_head=None, final_head=None, origin_head=None,
                          git_status_summary=None,
                          real_getme_attempted=False):
    """Build the deterministic, redacted evidence packet (pure value).

    Contains ONLY redacted, non-secret material: outcome classes, presence
    classes, checksums, and boolean proofs. NO token, NO raw response, NO raw
    URL, NO header, NO cookie.
    """
    # Credential env-var presence, redacted to a boolean. "Present" means the
    # gated read happened and did NOT fail with credential_missing.
    cred_outcome = proof.get("credential_proof_outcome_class")
    env_read_performed = bool(proof.get("env_read_performed"))
    credential_missing = pilot.BLOCK_CREDENTIAL_MISSING in (
        proof.get("blocked_reasons") or [])
    credential_env_var_present = bool(
        env_read_performed and not credential_missing)

    budget_used = 1 if identity.get("read_only_request_performed") else 0

    packet = {
        "task_label": TASK_LABEL,
        "model": RUNNER_MODEL,
        "model_version": RUNNER_MODEL_VERSION,
        "evidence_schema": EVIDENCE_SCHEMA,
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "status": pilot.Status.PASS,
        "provider": pilot.PROVIDER_TELEGRAM,
        # HEAD / baseline evidence.
        "required_baseline_commit": REQUIRED_BASELINE_COMMIT,
        "start_head": start_head,
        "final_head": final_head,
        "origin_head": origin_head,
        "baseline_matched": start_head == REQUIRED_BASELINE_COMMIT,
        "git_status_summary": git_status_summary,
        # What was attempted.
        "real_getme_attempted": bool(real_getme_attempted),
        "credential_env_var_present_redacted": credential_env_var_present,
        "credential_proof_outcome_class": cred_outcome,
        "only_one_env_var_read": bool(proof.get("only_one_env_var_read")),
        "allowed_env_var_name": pilot.ALLOWED_ENV_VAR,
        "request_budget_authorized": pilot.REQUEST_BUDGET,
        "request_budget_used": budget_used,
        # Redacted identity outcome.
        "identity_proof_outcome_class": identity.get(
            "identity_proof_outcome_class"),
        "getme_ok": bool(identity.get("getme_ok")),
        "provider_status_code_class": identity.get(
            "provider_status_code_class"),
        "response_status_class": identity.get("response_status_class"),
        "bot_identity_presence_class": identity.get(
            "bot_identity_redacted_class"),
        "bot_username_presence_class": identity.get(
            "bot_username_redacted_class"),
        # Checksums.
        "request_checksum": plan.get("request_plan_checksum"),
        "response_checksum": identity.get("response_checksum"),
        "identity_proof_checksum": identity.get("identity_proof_checksum"),
        "audit_checksum": audit.get("audit_checksum"),
        "audit_outcome_class": audit.get("audit_outcome_class"),
        # No-secret proofs (mirrored from the redacted artifacts).
        "stores_no_token": (
            proof.get("token_returned") is False
            and proof.get("token_logged") is False
            and proof.get("token_persisted") is False
            and audit.get("stores_token") is False),
        "stores_no_raw_response": (
            identity.get("stores_raw_response_body") is False
            and audit.get("stores_raw_response") is False),
        "stores_no_raw_url": (
            identity.get("stores_raw_url_with_token") is False
            and audit.get("stores_raw_url") is False),
        "stores_no_headers": (
            identity.get("stores_headers") is False
            and audit.get("stores_headers") is False),
        "stores_no_cookies": (
            identity.get("stores_cookies") is False
            and audit.get("stores_cookies") is False),
        # No-posting proofs.
        "no_sendmessage": identity.get("sendmessage_performed") is False,
        "no_posting": identity.get("posting_performed") is False,
        "no_autonomous_reply": identity.get(
            "autonomous_reply_performed") is False,
        "no_auto_retry": identity.get("auto_retry_allowed") is False,
        "no_scheduler": identity.get("scheduler_enabled") is False,
        "no_webhook": identity.get("webhook_registered") is False,
        "no_polling": identity.get("polling_enabled") is False,
        "not_valid_for_live_execution": identity.get(
            "valid_for_live_execution") is False,
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
    }
    packet["evidence_checksum"] = pilot.compute_checksum(packet)
    return packet


def build_evidence_doc(packet):
    """Render a deterministic, scanner-safe markdown evidence document."""
    attempted = "yes" if packet["real_getme_attempted"] else "no"
    present = "yes" if packet["credential_env_var_present_redacted"] else "no"
    return (
        f"# 0174UH/UI/UJ Telegram Real getMe Identity Proof\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        f"## Run summary\n\n"
        f"- Required baseline: `{packet['required_baseline_commit']}`\n"
        f"- Start HEAD: `{packet['start_head']}`\n"
        f"- Final HEAD: `{packet['final_head']}`\n"
        f"- Origin HEAD: `{packet['origin_head']}`\n"
        f"- Baseline matched: `{packet['baseline_matched']}`\n"
        f"- Real getMe attempted: `{attempted}`\n"
        f"- Credential env var present (redacted): `{present}`\n"
        f"- Credential proof outcome: `{packet['credential_proof_outcome_class']}`\n"
        f"- Request budget used: `{packet['request_budget_used']}` of "
        f"`{packet['request_budget_authorized']}`\n\n"
        f"## Redacted identity outcome\n\n"
        f"- Identity outcome class: `{packet['identity_proof_outcome_class']}`\n"
        f"- getMe ok: `{packet['getme_ok']}`\n"
        f"- Provider status code class: `{packet['provider_status_code_class']}`\n"
        f"- Response status class: `{packet['response_status_class']}`\n"
        f"- Bot identity presence class: `{packet['bot_identity_presence_class']}`\n"
        f"- Bot username presence class: `{packet['bot_username_presence_class']}`\n\n"
        f"## Checksums\n\n"
        f"- Request checksum: `{packet['request_checksum']}`\n"
        f"- Response checksum: `{packet['response_checksum']}`\n"
        f"- Identity proof checksum: `{packet['identity_proof_checksum']}`\n"
        f"- Audit checksum: `{packet['audit_checksum']}`\n"
        f"- Evidence checksum: `{packet['evidence_checksum']}`\n\n"
        f"## Safety proofs\n\n"
        f"- Stores no token: `{packet['stores_no_token']}`\n"
        f"- Stores no raw response: `{packet['stores_no_raw_response']}`\n"
        f"- Stores no raw URL: `{packet['stores_no_raw_url']}`\n"
        f"- Stores no headers: `{packet['stores_no_headers']}`\n"
        f"- Stores no cookies: `{packet['stores_no_cookies']}`\n"
        f"- No sendMessage: `{packet['no_sendmessage']}`\n"
        f"- No posting: `{packet['no_posting']}`\n"
        f"- No autonomous reply: `{packet['no_autonomous_reply']}`\n"
        f"- No auto retry: `{packet['no_auto_retry']}`\n"
        f"- No scheduler: `{packet['no_scheduler']}`\n"
        f"- No webhook: `{packet['no_webhook']}`\n"
        f"- No polling: `{packet['no_polling']}`\n"
        f"- Not valid for live execution: "
        f"`{packet['not_valid_for_live_execution']}`\n\n"
        f"## Next recommended task\n\n`{packet['next_recommended_task']}`\n")


def scan_evidence(packet, doc):
    """Return the combined list of redaction violations across packet + doc."""
    return pilot.scan_for_leaks(packet) + pilot.scan_for_leaks(doc)


def scan_for_financial_advice_safe(packet, doc):
    """Return the combined list of financial-advice violations across artifacts."""
    return (pilot.scan_for_financial_advice(packet)
            + pilot.scan_for_financial_advice(doc))


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
    packet_path.write_text(pilot.serialize(packet), encoding="utf-8",
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
    """Perform the real operator-owned read-only getMe identity proof run.

    Live read-only is ENABLED here (this is the operator-run task). The accepted
    pilot performs the single gated env read + EXACTLY one real ``getMe``. If the
    credential is missing or the request fails, a redacted blocked packet is
    still produced -- with no retry.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    start_head = _head("HEAD")

    plan, proof, identity, audit = run_identity_proof(
        operator_live_read_only_enabled=True)

    final_head = _head("HEAD")
    origin_head = _head("origin/master")
    status_summary = _git_status_summary()

    packet = build_evidence_packet(
        plan, proof, identity, audit, start_head=start_head,
        final_head=final_head, origin_head=origin_head,
        git_status_summary=status_summary, real_getme_attempted=True)
    doc = build_evidence_doc(packet)

    written = write_evidence(ROOT, packet, doc)

    # Console output is redacted: only outcome classes + booleans, never the
    # token or the raw provider response.
    print("TASK " + TASK_LABEL)
    print("REAL_GETME_ATTEMPTED " + str(packet["real_getme_attempted"]))
    print("CREDENTIAL_ENV_VAR_PRESENT_REDACTED "
          + str(packet["credential_env_var_present_redacted"]))
    print("IDENTITY_OUTCOME " + str(packet["identity_proof_outcome_class"]))
    print("PROVIDER_CODE_CLASS " + str(packet["provider_status_code_class"]))
    print("BUDGET_USED " + str(packet["request_budget_used"]))
    print("EVIDENCE_SCAN_CLEAN")
    for path in written:
        print("WROTE " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
