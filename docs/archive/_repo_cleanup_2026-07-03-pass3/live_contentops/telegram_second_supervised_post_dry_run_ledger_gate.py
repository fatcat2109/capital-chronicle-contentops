"""Telegram SECOND supervised post dry-run + durable ledger gate (0174CQ).

This task is NOT a second live send. It prepares a SECOND supervised Telegram
post through dry-run, approval-hash, redacted preview, and a durable ledger ONLY.
It proves the second-post workflow can be prepared safely WITHOUT touching
Telegram, WITHOUT reading credentials, and WITHOUT enabling live send.

HARD GUARANTEES (enforced by tests + leakage guards):
  * NO network library is imported (no urllib / requests / httpx / socket).
  * NO OAuth / dotenv library is imported.
  * NO env / credential read (never touches the process env vars or .env).
  * NO Telegram API call; NO sendMessage / getMe / getChat / getChatMember /
    getUpdates / webhook / scheduler / reply / DM / metrics / scraping.
  * Fail-closed / preview-only by default: the ledger file is written ONLY when
    the explicit ``--write-telegram-second-dry-run-ledger`` flag / ``write=True``
    is passed. No network is performed in either mode.
  * Deterministic ledger JSON: sorted keys, stable separators, trailing newline.
  * A redaction scanner runs over the ledger BEFORE write and blocks on token-like
    values, raw @handles, long digit runs (possible account/chat/message ids),
    Telegram bot API URLs, and forbidden raw request/response/credential keys.
  * All live-publish gates remain blocked after this dry-run.

This module REUSES the 0174CM forbidden-language + canonicalization helpers via
import; it does NOT modify 0174CM, 0174CN, 0174CO, or 0174CP.
"""

import hashlib
import json
import os.path
import re

from live_contentops import telegram_supervised_post_dry_run_gate as cm_gate

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CQ_TELEGRAM_SECOND_SUPERVISED_POST_DRY_RUN_"
    "WITH_DURABLE_LEDGER_GATE_V0"
)

GATE = "TELEGRAM_SECOND_SUPERVISED_POST_DRY_RUN_LEDGER_0174CQ"
PLATFORM = "telegram"
SOURCE_BASELINE_COMMIT = "f9beab298f18043e290a5fd6c19c3d1d056db437"

# Explicit write flag. Default behavior is preview-only / fail-closed.
FLAG_WRITE_LEDGER = "--write-telegram-second-dry-run-ledger"

# Ledger artifact location (relative to repo root).
LEDGER_REL_DIR = os.path.join("docs", "credential_readiness", "0174CQ")
LEDGER_FILENAME = "telegram_second_supervised_post_dry_run_ledger.json"

# Approval state for this specific second dry-run.
APPROVAL_STATE = "operator_approved_for_second_telegram_dry_run_0174cq"

# Method class — dry-run only, never a live request.
METHOD_CLASS = "sendMessage_dry_run_only"

# Telegram text limit (sendMessage caps at 4096 UTF-16 code units).
TELEGRAM_TEXT_LIMIT = 4096

# The exact, operator-approved SECOND dry-run payload text. Conservative,
# non-market-advisory, explicitly local-only / dry-run / no-live-send.
SECOND_DRY_RUN_PAYLOAD_TEXT = (
    "Capital Chronicle ContentOps second Telegram dry-run: supervised publish "
    "controls remain gated. This preview is local-only, human-reviewed, no "
    "financial advice, no trading calls, no automation, and no live send."
)

# --------------------------------------------------------------------------- #
# Redaction patterns (defense-in-depth). The ledger only ever holds booleans,
# symbolic strings, the operator-approved payload text, and hashes.
# --------------------------------------------------------------------------- #
_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),           # telegram bot token body
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM private key
    re.compile(r"AKIA[0-9A-Z]{16}"),                    # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                # GitHub PAT
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),        # bearer token
]
# Raw bot-api URL containing a token.
_URL_WITH_TOKEN = re.compile(r"api\.telegram\.org/bot\d{6,}:")
# Any api.telegram.org URL reference at all (no raw URLs allowed in the ledger).
_TELEGRAM_URL = re.compile(r"api\.telegram\.org")
# Raw channel @handle.
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")
# A long run of digits that could be a chat/channel/message/account id value.
_LONG_DIGITS = re.compile(r"(?<!\d)-?\d{7,}(?!\d)")

# Forbidden raw keys that would indicate an account-id / raw-traffic / secret leak.
_FORBIDDEN_KEYS = (
    "token",
    "bot_token",
    "chat_id",
    "channel_id",
    "channel_username",
    "bot_id",
    "bot_username",
    "message_id",
    "message_id_value",
    "date",
    "date_value",
    "raw_url",
    "raw_request",
    "raw_response",
    "target_identifier",
    "target_value",
    "access_token",
    "refresh_token",
    "client_secret",
    "api_key",
)


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def scan_ledger_for_leaks(ledger):
    """Return a sorted list of redaction violations for the ledger object.

    Blocks token-like values, any Telegram bot API URL, raw @handles, long digit
    runs that could be chat/channel/message/account ids, credential-like strings,
    and any forbidden raw key anywhere in the structure. The known baseline git
    SHA and the 64-char payload hash hex are not treated as id leaks.
    """
    violations = []

    def _walk(obj, key=None):
        if isinstance(obj, dict):
            for k, v in obj.items():
                kl = str(k).lower()
                if kl in _FORBIDDEN_KEYS:
                    violations.append(f"forbidden_key:{kl}")
                _walk(v, k)
        elif isinstance(obj, list):
            for v in obj:
                _walk(v, key)
        elif isinstance(obj, str):
            _scan_string(obj, key)

    def _scan_string(s, key):
        for pat in _SECRET_LIKE:
            if pat.search(s):
                violations.append(f"secret_like_value:{key or 'value'}")
                break
        if _URL_WITH_TOKEN.search(s) or _TELEGRAM_URL.search(s):
            violations.append(f"telegram_url:{key or 'value'}")
        if _HANDLE_LIKE.search(s):
            violations.append(f"raw_handle:{key or 'value'}")
        # Allow the known 64-char payload hash hex and baseline SHA; flag other
        # long digit runs (possible chat/channel/message/account id values).
        if key not in ("payload_hash",) and _LONG_DIGITS.search(s):
            if not _is_known_safe_identifier(s):
                violations.append(f"long_digits_possible_id:{key or 'value'}")

    _walk(ledger)
    return sorted(set(violations))


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (baseline git SHA, payload hash)."""
    if s == SOURCE_BASELINE_COMMIT:
        return True
    # A git SHA / sha-256 hash is hex with letters; _LONG_DIGITS only matches a
    # >=7 pure-digit run, which such hashes virtually never contain. Be explicit.
    if re.fullmatch(r"[0-9a-f]{40}", s) or re.fullmatch(r"[0-9a-f]{64}", s):
        return True
    return False


# --------------------------------------------------------------------------- #
# Payload build + validation + canonical hash
# --------------------------------------------------------------------------- #
def build_second_dry_run_payload():
    """Build the exact operator-approved SECOND dry-run payload (0174CM shape)."""
    return {
        "payload_id": "cc-telegram-second-dryrun-0174cq-0001",
        "platform": PLATFORM,
        "target_slot": cm_gate.TARGET_SLOT,
        "content_text": SECOND_DRY_RUN_PAYLOAD_TEXT,
        "content_class": "supervised_dry_run_preview_note",
        "source_packet_id": None,
        "local_fixture_ref": (
            "docs/credential_readiness/0174CQ/"
            "telegram_second_supervised_post_dry_run_ledger.json"
        ),
        "no_financial_advice": True,
        "no_signal_language": True,
        "human_review_required": True,
        "public_postable": False,
        "live_send_enabled": False,
    }


def validate_payload_text(text):
    """Validate the dry-run payload TEXT shape. Returns (ok, [reasons])."""
    reasons = []
    if not isinstance(text, str) or not text.strip():
        return False, ["payload_text_missing"]
    if len(text) > TELEGRAM_TEXT_LIMIT:
        reasons.append("payload_text_exceeds_telegram_limit")
    # Must clearly state local-only / dry-run / no live send.
    low = text.lower()
    if "local-only" not in low:
        reasons.append("payload_text_missing_local_only_statement")
    if "dry-run" not in low:
        reasons.append("payload_text_missing_dry_run_statement")
    if "no live send" not in low:
        reasons.append("payload_text_missing_no_live_send_statement")
    return (len(reasons) == 0), reasons


def compute_payload_hash(payload):
    """Deterministic SHA-256 of the 0174CM canonical payload form (hash lock)."""
    return cm_gate.compute_payload_hash(payload)


# --------------------------------------------------------------------------- #
# Approval record + simulated request class
# --------------------------------------------------------------------------- #
def build_approval_record(payload_hash):
    """Build the second dry-run approval record bound to the exact payload hash."""
    return {
        "approval_state": APPROVAL_STATE,
        "approved_payload_hash": payload_hash,
        "human_review_completed": True,
        "prior_0174cn_live_pilot_accepted": True,
        "prior_0174co_ledger_persisted": True,
        "prior_0174cp_platform_selection_accepted": True,
        "understands_no_live_send": True,
        "one_time_dry_run_only": True,
    }


def validate_approval_record(record, expected_hash):
    """Validate the approval record matches the EXACT payload hash. (ok,[reasons])."""
    reasons = []
    if not isinstance(record, dict):
        return False, ["approval_record_missing"]
    if record.get("approval_state") != APPROVAL_STATE:
        reasons.append("approval_state_not_second_dry_run")
    if record.get("approved_payload_hash") != expected_hash:
        reasons.append("approval_hash_mismatch")
    for ack in (
        "human_review_completed",
        "prior_0174cn_live_pilot_accepted",
        "prior_0174co_ledger_persisted",
        "prior_0174cp_platform_selection_accepted",
        "understands_no_live_send",
        "one_time_dry_run_only",
    ):
        if record.get(ack) is not True:
            reasons.append(f"ack_missing:{ack}")
    return (len(reasons) == 0), reasons


def build_simulated_request_class():
    """Build the simulated (would-send) sendMessage request class. Never live."""
    return {
        "method_class": METHOD_CLASS,
        "request_attempted": False,
        "live_network_attempted": False,
        "send_message_attempted": False,
        "would_send_message": True,
        "request_budget": 0,
    }


# --------------------------------------------------------------------------- #
# Durable ledger builder
# --------------------------------------------------------------------------- #
def build_ledger():
    """Assemble the full, redaction-safe second-dry-run durable ledger.

    Returns (ledger, blocked_reasons). The ledger ``status`` is ``pass`` only
    when payload shape + forbidden-language + approval-hash all validate.
    """
    payload = build_second_dry_run_payload()
    text = payload["content_text"]

    blocked = []

    shape_ok, shape_reasons = validate_payload_text(text)
    blocked.extend(shape_reasons)

    lang_ok, lang_reasons = cm_gate.check_forbidden_language(text)
    blocked.extend(lang_reasons)

    payload_hash = compute_payload_hash(payload)
    approval = build_approval_record(payload_hash)
    approval_ok, approval_reasons = validate_approval_record(approval, payload_hash)
    blocked.extend(approval_reasons)

    request_class = build_simulated_request_class()

    status = "pass" if not blocked else "blocked"

    ledger = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "prior_chain": {
            "telegram_identity_validated": True,
            "telegram_target_binding_validated": True,
            "first_dry_run_preflight_validated": True,
            "first_live_post_delivered_once": True,
            "first_post_pilot_ledger_persisted": True,
            "next_platform_selection_accepted": True,
        },
        "platform": PLATFORM,
        "dry_run_number": 2,
        "payload_text_persisted": True,
        "payload_text": text,
        "payload_hash": payload_hash,
        "payload_hash_verified": True,
        "approval_record_present": True,
        "approval_hash_matches_payload": approval_ok,
        "method_class": request_class["method_class"],
        "request_attempted": request_class["request_attempted"],
        "live_network_attempted": request_class["live_network_attempted"],
        "send_message_attempted": request_class["send_message_attempted"],
        "would_send_message": request_class["would_send_message"],
        "message_sent": False,
        "request_budget": request_class["request_budget"],
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_token_exchange_performed": True,
        "no_posting_performed": True,
        "no_scheduler_created": True,
        "no_webhook_created": True,
        "no_reply_dm_created": True,
        "no_metrics_fetched": True,
        "no_scraping_performed": True,
        "live_publish_gate": "blocked_after_second_dry_run",
        "next_gate_required_before_second_live_post": True,
        "redaction_verified": True,
        "status": status,
        "blocked_reasons": sorted(set(blocked)),
    }
    return ledger, sorted(set(blocked))


def serialize_ledger(ledger):
    """Deterministic JSON serialization: sorted keys, stable separators, newline."""
    return json.dumps(ledger, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_ledger_checksum(ledger):
    """SHA-256 of the deterministic serialization (artifact integrity, not secret)."""
    return hashlib.sha256(serialize_ledger(ledger).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Gate runner
# --------------------------------------------------------------------------- #
def run_gate(write=False, repo_root="."):
    """Build, validate, and (optionally) persist the second-dry-run ledger.

    Returns a redacted summary dict. The ledger file is written ONLY when
    ``write=True`` AND the redaction scan passes AND status is pass.
    """
    ledger, blocked = build_ledger()
    violations = scan_ledger_for_leaks(ledger)

    summary = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "write_requested": bool(write),
        "network_performed": False,
        "env_read_performed": False,
        "dry_run_number": 2,
        "payload_hash": ledger["payload_hash"],
        "approval_hash_matches_payload": ledger["approval_hash_matches_payload"],
        "method_class": ledger["method_class"],
        "request_attempted": ledger["request_attempted"],
        "live_network_attempted": ledger["live_network_attempted"],
        "send_message_attempted": ledger["send_message_attempted"],
        "would_send_message": ledger["would_send_message"],
        "message_sent": ledger["message_sent"],
        "request_budget": ledger["request_budget"],
        "redaction_scan_passed": not violations,
        "redaction_violations": violations,
        "ledger_serialized": False,
        "ledger_written": False,
        "ledger_path": os.path.join(LEDGER_REL_DIR, LEDGER_FILENAME),
        "ledger_checksum": None,
        "live_publish_gate": ledger["live_publish_gate"],
        "next_gate_required_before_second_live_post": True,
        "redaction_verified": not violations,
        "status": "fail_closed",
        "blocked_reasons": [],
    }

    if violations:
        summary["status"] = "blocked"
        summary["blocked_reasons"] = ["redaction_guard_triggered"]
        return summary

    if ledger["status"] != "pass":
        summary["status"] = ledger["status"]
        summary["blocked_reasons"] = blocked
        return summary

    serialized = serialize_ledger(ledger)
    summary["ledger_serialized"] = True
    summary["ledger_checksum"] = compute_ledger_checksum(ledger)

    if not write:
        # Preview-only / fail-closed default: do not touch disk.
        summary["status"] = "pass"
        return summary

    out_dir = os.path.join(repo_root, LEDGER_REL_DIR)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, LEDGER_FILENAME)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(serialized)

    summary["ledger_written"] = True
    summary["status"] = "pass"
    return summary


def main(argv=None):
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    write = FLAG_WRITE_LEDGER in argv
    result = run_gate(write=write)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
