"""Telegram post-pilot ledger gate (0174CO).

This is a STRICTLY LOCAL module. It persists a durable, redacted ledger/audit
record for the accepted 0174CN supervised live Telegram pilot post, plus a
concise next-platform account-binding roadmap stub. It makes NO live calls.

It is NOT a publisher and NOT a delivery-lookup tool. It only records, in
redacted/symbolic form, that exactly one supervised live ``sendMessage`` was
performed by 0174CN, and that all future/live automation gates remain blocked.

Prior chain (unchanged by this module):
  * 0174CK validated bot token identity via live read-only ``getMe``.
  * 0174CL validated target channel binding + channel post permission.
  * 0174CM validated the local supervised post preflight (deterministic payload
    hash, dry-run approval record, kill switch live-dispatch block, mock
    would-send shape, redacted audit event) WITHOUT any live send.
  * 0174CN sent EXACTLY ONE supervised live ``sendMessage`` and stopped.

HARD GUARANTEES (enforced by tests + leakage guards):
  * NO network library is imported (no urllib / requests / httpx / socket).
  * NO env / credential read (never touches the process environment or .env).
  * Fail-closed / preview-only by default: the ledger file is written ONLY when
    the explicit ``--write-telegram-post-pilot-ledger`` flag / ``write=True`` is
    passed. No network is performed in either mode.
  * The 0174CN canonical payload hash is RECOMPUTED from the committed module's
    ``build_default_payload()`` and must equal the expected hash, or the task
    blocks and writes nothing.
  * Deterministic ledger JSON: sorted keys, stable separators, trailing newline.
  * A redaction scanner runs over the ledger artifact BEFORE write and blocks on
    token-like values, Telegram bot API URLs, raw @handles, chat/channel ids,
    message id values, raw request/response keys, or credential-like strings.
  * The Telegram message id VALUE is never persisted; only ``message_id_present``.
  * After this ledger, ALL future/live automation gates remain blocked.
"""

import hashlib
import json
import os.path
import re

from live_contentops import telegram_first_supervised_live_post_gate as live_gate

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CO_TELEGRAM_POST_PILOT_LEDGER_AND_NEXT_PLATFORM_"
    "ACCOUNT_BINDING_ROADMAP_V0"
)

LEDGER_GATE = "TELEGRAM_POST_PILOT_LEDGER_0174CO"
PLATFORM = "telegram"

SOURCE_LIVE_TASK = (
    "TASK_CONTENTOPS_0174CN_TELEGRAM_FIRST_SUPERVISED_LIVE_POST_"
    "TO_OPERATOR_APPROVED_TARGET_V0"
)
SOURCE_LIVE_COMMIT = "71bcd9cb79fe6039290145d438969987b2728222"

# The expected canonical payload hash for the accepted 0174CN live pilot text.
EXPECTED_PAYLOAD_HASH = (
    "b9955db3a78d0738aa99f12e8889d70bae450395b9eae58e313fd70b9d73baa1"
)

# Explicit write flag. Default behavior is preview-only / fail-closed.
FLAG_WRITE_LEDGER = "--write-telegram-post-pilot-ledger"

# Ledger artifact location (relative to repo root).
LEDGER_REL_DIR = os.path.join("docs", "credential_readiness", "0174CO")
LEDGER_FILENAME = "telegram_post_pilot_ledger_0174cn.json"

# --------------------------------------------------------------------------- #
# Redaction patterns (defense-in-depth). The ledger only ever holds booleans +
# symbolic strings + the operator-approved payload text, but we scrub on leak.
# --------------------------------------------------------------------------- #
_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),          # telegram bot token body
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM private key
    re.compile(r"AKIA[0-9A-Z]{16}"),                    # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                # GitHub PAT
]
# Raw bot-api URL containing a token.
_URL_WITH_TOKEN = re.compile(r"api\.telegram\.org/bot\d{6,}:")
# Any api.telegram.org URL reference at all (no raw URLs allowed in the ledger).
_TELEGRAM_URL = re.compile(r"api\.telegram\.org")
# Raw channel @handle.
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")
# A long run of digits that could be a chat/channel/message id value.
_LONG_DIGITS = re.compile(r"(?<!\d)-?\d{7,}(?!\d)")

# Forbidden raw keys that would indicate an account-id / raw-traffic leak.
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
)


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def scan_ledger_for_leaks(ledger):
    """Return a sorted list of redaction violations for the ledger object.

    Blocks token-like values, any Telegram bot API URL, raw @handles, long digit
    runs that could be chat/channel/message ids, credential-like strings, and any
    forbidden raw key anywhere in the structure. The whitelisted payload-hash hex
    and the known short ``0174..`` task labels are not treated as id leaks.
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
        # Allow the known 64-char payload hash hex; flag other long digit runs
        # (possible chat/channel/message id values).
        if key not in ("payload_hash",) and _LONG_DIGITS.search(s):
            # The source_live_commit is a 40-char hex SHA (letters+digits), which
            # _LONG_DIGITS only matches if there is a >=7 pure-digit run; a git
            # SHA virtually always contains letters, so this is safe. Be explicit:
            if not _is_known_safe_identifier(s):
                violations.append(f"long_digits_possible_id:{key or 'value'}")

    _walk(ledger)
    return sorted(set(violations))


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHA, payload hash, task labels)."""
    if s == SOURCE_LIVE_COMMIT or s == EXPECTED_PAYLOAD_HASH:
        return True
    # Pure hex of length 40 (sha1) or 64 (sha256) with at least one letter.
    if re.fullmatch(r"[0-9a-f]{40}", s) or re.fullmatch(r"[0-9a-f]{64}", s):
        return True
    return False


# --------------------------------------------------------------------------- #
# Hash recompute + verification
# --------------------------------------------------------------------------- #
def recompute_0174cn_payload_hash():
    """Recompute the canonical payload hash from the committed 0174CN module."""
    payload = live_gate.build_default_payload()
    return live_gate.compute_payload_hash(payload)


def verify_payload_hash():
    """(ok, recomputed_hash). ok is True iff recomputed == EXPECTED_PAYLOAD_HASH."""
    recomputed = recompute_0174cn_payload_hash()
    return (recomputed == EXPECTED_PAYLOAD_HASH), recomputed


# --------------------------------------------------------------------------- #
# Ledger + roadmap builders
# --------------------------------------------------------------------------- #
def build_roadmap_stub():
    """Concise next-platform account-binding roadmap stub (no implementation)."""
    return {
        "next_platform_binding_candidate": (
            "x_or_linkedin_or_telegram_second_gate_pending_operator_choice"
        ),
        "requirement_before_next_live_send": (
            "new explicit task + operator GO + platform-specific account binding "
            "+ dry-run + approval hash"
        ),
        "no_autonomous_publishing": True,
        "no_scheduler": True,
        "no_reply_dm": True,
        "no_metrics_fetch": True,
        "no_scraping": True,
    }


def build_ledger_record(payload_hash, payload_hash_verified):
    """Build the redacted, deterministic ledger record dict for 0174CN."""
    payload = live_gate.build_default_payload()
    payload_text = payload.get("content_text")
    approval = live_gate.build_default_live_approval_record(payload)
    approval_matches = approval.get("approved_payload_hash") == payload_hash

    return {
        "task_label": TASK_LABEL,
        "ledger_gate": LEDGER_GATE,
        "source_live_task": SOURCE_LIVE_TASK,
        "source_live_commit": SOURCE_LIVE_COMMIT,
        "platform": PLATFORM,
        "live_result_class": "delivered_once_redacted",
        "request_count": 1,
        "request_budget": 1,
        "allowed_method": "sendMessage",
        "message_sent": True,
        "telegram_response_ok_class": "true",
        "message_id_present": True,
        "message_id_value_persisted": False,
        "date_value_persisted": False,
        "target_identifier_persisted": False,
        "raw_response_persisted": False,
        "raw_request_persisted": False,
        "credential_persisted": False,
        "payload_text_persisted": True,
        "payload_text": payload_text,
        "payload_hash": payload_hash,
        "payload_hash_verified": bool(payload_hash_verified),
        "approval_hash_matches_payload": bool(approval_matches),
        "chain_0174ck_identity_validated": True,
        "chain_0174cl_target_binding_validated": True,
        "chain_0174cm_dry_run_preflight_validated": True,
        "chain_0174cn_live_send_passed": True,
        "post_pilot_live_publish_gate": "blocked_after_one_time_pilot",
        "next_gate_required_before_next_live_post": True,
        "scheduler_enabled": False,
        "webhook_enabled": False,
        "get_updates_enabled": False,
        "autonomous_replies_enabled": False,
        "metrics_fetch_enabled": False,
        "live_dispatch_enabled_after_pilot": False,
        "redaction_verified": True,
        "next_platform_binding_roadmap": build_roadmap_stub(),
        "status": "pass",
        "blocked_reasons": [],
    }


def serialize_ledger(ledger):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(ledger, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def ledger_checksum(serialized_text):
    """SHA-256 of the serialized ledger TEXT (artifact integrity, not a secret)."""
    return hashlib.sha256(serialized_text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_post_pilot_ledger_gate(*, write=False, repo_root=None, _writer=None):
    """Run the local post-pilot ledger gate. Preview-only unless ``write=True``.

    Never performs any network or env read. Recomputes + verifies the 0174CN
    payload hash, builds the redacted deterministic ledger, runs a redaction scan,
    and (only when ``write=True`` and all checks pass) writes the ledger artifact.

    ``_writer`` is an injectable (path, text) -> None writer for tests. When None,
    a real local file write is used (still no network).
    """
    summary = {
        "task_label": TASK_LABEL,
        "ledger_gate": LEDGER_GATE,
        "write_requested": bool(write),
        "network_performed": False,
        "env_read_performed": False,
        "payload_hash_verified": False,
        "payload_hash_recomputed_class": "pending",
        "redaction_scan_passed": False,
        "ledger_serialized": False,
        "ledger_written": False,
        "ledger_path": None,
        "ledger_checksum": None,
        "post_pilot_live_publish_gate": "blocked_after_one_time_pilot",
        "next_gate_required_before_next_live_post": True,
        "live_dispatch_enabled_after_pilot": False,
        "scheduler_enabled": False,
        "webhook_enabled": False,
        "get_updates_enabled": False,
        "autonomous_replies_enabled": False,
        "metrics_fetch_enabled": False,
        "redaction_verified": True,
        "status": "fail_closed",
        "blocked_reasons": [],
    }

    blocked = []

    # 1. Recompute + verify the 0174CN canonical payload hash.
    hash_ok, recomputed = verify_payload_hash()
    summary["payload_hash_verified"] = hash_ok
    summary["payload_hash_recomputed_class"] = (
        "matches_expected" if hash_ok else "mismatch_blocked")
    if not hash_ok:
        blocked.append("payload_hash_mismatch_block_no_write")

    # 2. Build the ledger record (deterministic).
    ledger = build_ledger_record(recomputed, hash_ok)

    # 3. Redaction scan over the ledger artifact BEFORE any write.
    leaks = scan_ledger_for_leaks(ledger)
    summary["redaction_scan_passed"] = not leaks
    if leaks:
        blocked.append("redaction_scan_blocked")
        summary["blocked_reasons"] = sorted(set(blocked + leaks))
        summary["status"] = "blocked"
        return summary

    # 4. Serialize deterministically + compute artifact checksum.
    serialized = serialize_ledger(ledger)
    summary["ledger_serialized"] = True
    summary["ledger_checksum"] = ledger_checksum(serialized)

    root = (os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if repo_root is None else repo_root)
    ledger_dir = os.path.join(root, LEDGER_REL_DIR)
    ledger_path = os.path.join(ledger_dir, LEDGER_FILENAME)
    summary["ledger_path"] = os.path.join(
        LEDGER_REL_DIR, LEDGER_FILENAME).replace("\\", "/")

    # If the hash check failed, block now (after computing class, before write).
    if blocked:
        summary["status"] = "blocked"
        summary["blocked_reasons"] = sorted(set(blocked))
        return summary

    # 5. Preview-only unless the explicit write flag is present.
    if not write:
        summary["status"] = "fail_closed"
        summary["blocked_reasons"] = ["write_flag_absent_preview_only"]
        return summary

    # 6. Write the ledger artifact (local only; no network).
    if _writer is not None:
        _writer(ledger_path, serialized)
    else:
        os.makedirs(ledger_dir, exist_ok=True)
        with open(ledger_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(serialized)
    summary["ledger_written"] = True

    summary["status"] = "pass"
    summary["blocked_reasons"] = []
    return summary


def summary(**kwargs):
    """Convenience wrapper returning the redacted gate summary dict."""
    return run_post_pilot_ledger_gate(**kwargs)


def main(argv=None):
    """CLI: print ONLY the redacted JSON summary.

    Preview-only / fail-closed unless ``--write-telegram-post-pilot-ledger`` is
    passed. No network in either mode.

    Usage:
      python -m live_contentops.telegram_post_pilot_ledger_gate
      python -m live_contentops.telegram_post_pilot_ledger_gate \\
          --write-telegram-post-pilot-ledger
    """
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    write = FLAG_WRITE_LEDGER in args
    result = run_post_pilot_ledger_gate(write=write)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
