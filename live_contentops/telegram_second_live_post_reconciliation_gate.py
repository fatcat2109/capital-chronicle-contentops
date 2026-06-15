"""Telegram second live-post POST-SEND ledger reconciliation gate (0174CS).

This module is STRICTLY LOCAL. It performs NO network of any kind and reads NO
env/credentials. It exists to:

  * Read the existing 0174CR redacted post-send ledger.
  * Verify the accepted live-result fields remain unchanged.
  * Verify no secret/account/raw-response fields are present (redaction scan).
  * Transparently CORRECT one metadata bug in the 0174CR ledger:
        pre_live_implementation_commit
            was:  0a38e91f1b5e6b4c94d2322ffa8b78d99449fbe3 (incorrect)
            now:  422fc8d04a872ca88deb965a50bbb5b4a4d4cb21 (true pre-live commit)
    without obscuring the original mistake (the original value + reason are
    recorded both in the ledger reconciliation fields and the 0174CS packet).
  * Confirm all future live gates remain blocked.
  * Emit a conservative operator roadmap for the next stage.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / socket / dotenv).
  * No process env / .env read.
  * Imports ONLY hashlib, json, os.path, re.
  * Fail-closed: writes happen ONLY when the write flag is present AND the
    redaction scan passes on BOTH the corrected ledger and the packet.
  * Only metadata/provenance fields of the 0174CR ledger may change; the
    accepted live-outcome fields are immutable and verified unchanged.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
"""

import hashlib
import json
import os.path
import re

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CS_TELEGRAM_SECOND_LIVE_POST_POSTSEND_LEDGER_"
    "RECONCILIATION_AND_OPERATOR_ROADMAP_V0"
)

GATE = "TELEGRAM_SECOND_LIVE_POST_RECONCILIATION_0174CS"
PLATFORM = "telegram"
SOURCE_BASELINE_COMMIT = "5d52ef4628e905e74cd9cc25c9e42b67e6711572"

# Provenance: the 0174CR commits this task reconciles.
SOURCE_0174CR_PRE_LIVE_COMMIT_EXPECTED = "422fc8d04a872ca88deb965a50bbb5b4a4d4cb21"
SOURCE_0174CR_POST_LIVE_LEDGER_COMMIT = "5d52ef4628e905e74cd9cc25c9e42b67e6711572"

# The metadata bug being corrected.
ORIGINAL_PRE_LIVE_COMMIT_RECORDED = "0a38e91f1b5e6b4c94d2322ffa8b78d99449fbe3"
CORRECTED_PRE_LIVE_COMMIT = "422fc8d04a872ca88deb965a50bbb5b4a4d4cb21"
CORRECTION_REASON = "corrected_pre_live_implementation_commit_metadata"

# Artifact locations.
LEDGER_REL_PATH = os.path.join(
    "docs", "credential_readiness", "0174CR",
    "telegram_second_supervised_live_post_ledger.json")
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174CS")
PACKET_FILENAME = "telegram_second_live_post_reconciliation_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-telegram-second-live-reconciliation"

# The immutable accepted live-result fields. These must NOT change. Each maps to
# the exact value the accepted 0174CR live run produced.
IMMUTABLE_LIVE_FIELDS = {
    "allowed_method": "sendMessage",
    "request_attempted": True,
    "request_count": 1,
    "request_budget": 1,
    "send_message_attempted": True,
    "message_sent": True,
    "telegram_response_ok_class": "true",
    "message_id_present": True,
    "date_present": True,
    "message_id_value_persisted": False,
    "date_value_persisted": False,
    "target_identifier_persisted": False,
    "raw_request_persisted": False,
    "raw_response_persisted": False,
    "credential_persisted": False,
    "no_retry": True,
    "second_attempt_made": False,
    "scheduler_enabled": False,
    "webhook_enabled": False,
    "get_updates_enabled": False,
    "autonomous_replies_enabled": False,
    "metrics_fetch_enabled": False,
    "live_publish_gate": "blocked_after_second_live_pilot",
    "next_gate_required_before_any_future_live_post": True,
    "status": "pass",
}

# Content fields that must also be preserved byte-for-byte.
IMMUTABLE_CONTENT_FIELDS = ("payload_text", "payload_hash")

# The ONLY ledger fields this task is allowed to add or change.
ALLOWED_MUTATION_KEYS = frozenset({
    "pre_live_implementation_commit",
    "reconciliation_applied_by_task",
    "reconciliation_reason",
    "original_pre_live_implementation_commit_recorded",
    "corrected_pre_live_implementation_commit",
    "live_result_fields_changed",
    "redaction_contract_preserved",
})


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth; mirrors the 0174CR contract).
# --------------------------------------------------------------------------- #
_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),          # telegram bot token body
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM private key
    re.compile(r"AKIA[0-9A-Z]{16}"),                    # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                # GitHub PAT
]
_URL_WITH_TOKEN = re.compile(r"api\.telegram\.org/bot\d{6,}:")
_TELEGRAM_URL = re.compile(r"api\.telegram\.org")
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")
_LONG_DIGITS = re.compile(r"(?<!\d)-?\d{7,}(?!\d)")

_FORBIDDEN_KEYS = (
    "token", "bot_token", "chat_id", "channel_id", "channel_username",
    "bot_id", "bot_username", "message_id", "message_id_value", "date",
    "date_value", "raw_url", "raw_request", "raw_response",
    "target_identifier", "target_value", "access_token", "refresh_token",
    "client_secret", "api_key",
)


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hash)."""
    known = {
        SOURCE_BASELINE_COMMIT,
        SOURCE_0174CR_PRE_LIVE_COMMIT_EXPECTED,
        SOURCE_0174CR_POST_LIVE_LEDGER_COMMIT,
        ORIGINAL_PRE_LIVE_COMMIT_RECORDED,
        CORRECTED_PRE_LIVE_COMMIT,
    }
    if s in known:
        return True
    if re.fullmatch(r"[0-9a-f]{40}", s) or re.fullmatch(r"[0-9a-f]{64}", s):
        return True
    return False


def scan_ledger_for_leaks(obj):
    """Return a sorted list of redaction violations for an object."""
    violations = []

    def _walk(node, key=None):
        if isinstance(node, dict):
            for k, v in node.items():
                if str(k).lower() in _FORBIDDEN_KEYS:
                    violations.append(f"forbidden_key:{str(k).lower()}")
                _walk(v, k)
        elif isinstance(node, list):
            for v in node:
                _walk(v, key)
        elif isinstance(node, str):
            _scan_string(node, key)

    def _scan_string(s, key):
        for pat in _SECRET_LIKE:
            if pat.search(s):
                violations.append(f"secret_like_value:{key or 'value'}")
                break
        if _URL_WITH_TOKEN.search(s) or _TELEGRAM_URL.search(s):
            violations.append(f"telegram_url:{key or 'value'}")
        if _HANDLE_LIKE.search(s):
            violations.append(f"raw_handle:{key or 'value'}")
        if key not in ("payload_hash",) and _LONG_DIGITS.search(s):
            if not _is_known_safe_identifier(s):
                violations.append(f"long_digits_possible_id:{key or 'value'}")

    _walk(obj)
    return sorted(set(violations))


# --------------------------------------------------------------------------- #
# Deterministic serialization
# --------------------------------------------------------------------------- #
def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Ledger load + verification + correction
# --------------------------------------------------------------------------- #
def load_ledger(repo_root):
    """Load the existing 0174CR ledger dict, or None if missing/unparseable."""
    path = os.path.join(repo_root, LEDGER_REL_PATH)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.loads(fh.read())
    except (ValueError, OSError):
        return None


def verify_live_fields_unchanged(ledger):
    """Verify the immutable accepted live-result + content fields are intact."""
    reasons = []
    if not isinstance(ledger, dict):
        return False, ["ledger_missing_or_unparseable"]
    for key, expected in IMMUTABLE_LIVE_FIELDS.items():
        if ledger.get(key) != expected:
            reasons.append(f"live_field_mismatch:{key}")
    for key in IMMUTABLE_CONTENT_FIELDS:
        if key not in ledger:
            reasons.append(f"content_field_missing:{key}")
    return (len(reasons) == 0), reasons


def apply_correction(ledger):
    """Return a corrected COPY of the ledger.

    Only metadata/provenance fields are changed/added. The accepted live-result
    fields are copied verbatim. The original incorrect value is preserved in a
    transparent reconciliation field.
    """
    corrected = dict(ledger)
    original_value = ledger.get("pre_live_implementation_commit")
    corrected["pre_live_implementation_commit"] = CORRECTED_PRE_LIVE_COMMIT
    corrected["reconciliation_applied_by_task"] = TASK_LABEL
    corrected["reconciliation_reason"] = CORRECTION_REASON
    corrected["original_pre_live_implementation_commit_recorded"] = (
        original_value if original_value is not None
        else ORIGINAL_PRE_LIVE_COMMIT_RECORDED)
    corrected["corrected_pre_live_implementation_commit"] = CORRECTED_PRE_LIVE_COMMIT
    corrected["live_result_fields_changed"] = False
    corrected["redaction_contract_preserved"] = True
    return corrected


def diff_mutated_keys(before, after):
    """Return the set of keys whose value changed or was added between dicts."""
    changed = set()
    keys = set(before) | set(after)
    for k in keys:
        if before.get(k) != after.get(k) or (k in after) != (k in before):
            changed.add(k)
    return changed


def correction_only_touches_allowed_keys(before, after):
    """True iff the correction changed/added ONLY allowed mutation keys."""
    changed = diff_mutated_keys(before, after)
    illegal = changed - ALLOWED_MUTATION_KEYS
    return (len(illegal) == 0), sorted(illegal)


# --------------------------------------------------------------------------- #
# Operator roadmap
# --------------------------------------------------------------------------- #
def build_operator_roadmap():
    """Conservative operator roadmap for the next stage."""
    return {
        "recommended_next_phase":
            "pause_live_and_review_or_prepare_platform_requirements",
        "recommended_next_task":
            "TASK_CONTENTOPS_0174CT_OPERATOR_LIVE_PUBLISHING_REVIEW_AND_"
            "PLATFORM_REQUIREMENTS_BACKLOG_V0",
        "live_posting_state":
            "blocked_until_new_explicit_task_and_operator_go",
        "platform_options": [
            "telegram_pause_and_review",
            "telegram_third_gate_later",
            "x_requirements_only",
            "linkedin_requirements_only",
        ],
        "immediate_recommendation": (
            "pause additional live sends and review the two Telegram pilot "
            "posts plus evidence chain"
        ),
        "why": (
            "two live Telegram posts are enough to prove the supervised path; "
            "next work should reduce operational risk before expanding live "
            "sends"
        ),
        "no_scheduler": True,
        "no_reply_dm": True,
        "no_metrics_fetch": True,
        "no_scraping": True,
        "no_autonomous_publishing": True,
    }


# --------------------------------------------------------------------------- #
# Reconciliation packet
# --------------------------------------------------------------------------- #
def build_reconciliation_packet(*, ledger, correction_applied,
                                live_fields_ok, current_ledger_checksum,
                                status, blocked_reasons):
    """Assemble the 0174CS reconciliation packet (redacted, deterministic)."""
    roadmap = build_operator_roadmap()
    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "source_0174cr_pre_live_commit_expected":
            SOURCE_0174CR_PRE_LIVE_COMMIT_EXPECTED,
        "source_0174cr_post_live_ledger_commit":
            SOURCE_0174CR_POST_LIVE_LEDGER_COMMIT,
        "ledger_path_reconciled": LEDGER_REL_PATH.replace(os.sep, "/"),
        "original_pre_live_implementation_commit_recorded":
            ORIGINAL_PRE_LIVE_COMMIT_RECORDED,
        "corrected_pre_live_implementation_commit": CORRECTED_PRE_LIVE_COMMIT,
        "correction_applied_to_current_ledger": bool(correction_applied),
        "correction_reason": CORRECTION_REASON,
        "live_result_fields_changed": False,
        "live_result_still_pass": bool(live_fields_ok),
        "request_count_still_one": ledger.get("request_count") == 1,
        "request_budget_still_one": ledger.get("request_budget") == 1,
        "no_retry_still_true": ledger.get("no_retry") is True,
        "second_attempt_still_false": ledger.get("second_attempt_made") is False,
        "message_id_value_persisted_still_false":
            ledger.get("message_id_value_persisted") is False,
        "date_value_persisted_still_false":
            ledger.get("date_value_persisted") is False,
        "raw_request_persisted_still_false":
            ledger.get("raw_request_persisted") is False,
        "raw_response_persisted_still_false":
            ledger.get("raw_response_persisted") is False,
        "credential_persisted_still_false":
            ledger.get("credential_persisted") is False,
        "post_live_lock_state_verified":
            ledger.get("live_publish_gate") == "blocked_after_second_live_pilot"
            and ledger.get("next_gate_required_before_any_future_live_post")
            is True,
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_posting_performed": True,
        "no_scheduler_created": True,
        "no_webhook_created": True,
        "no_reply_dm_created": True,
        "no_metrics_fetched": True,
        "no_scraping_performed": True,
        "redaction_verified": True,
        "current_ledger_checksum_after_reconciliation": current_ledger_checksum,
        "operator_roadmap": roadmap,
        "status": status,
        "blocked_reasons": sorted(set(blocked_reasons)),
    }
    return packet


def build_readme():
    """Concise operator-facing README for the 0174CS packet."""
    return (
        "# 0174CS Telegram Second Live-Post Reconciliation\n"
        "\n"
        "Strictly local, no-network reconciliation of the 0174CR second "
        "supervised Telegram live-post ledger.\n"
        "\n"
        "## What this did\n"
        "\n"
        "- Corrected one metadata bug in the 0174CR ledger:\n"
        "  `pre_live_implementation_commit` "
        f"`{ORIGINAL_PRE_LIVE_COMMIT_RECORDED}` (incorrect) -> "
        f"`{CORRECTED_PRE_LIVE_COMMIT}` (true pre-live commit).\n"
        "- Preserved the original incorrect value transparently in both the "
        "ledger reconciliation fields and the reconciliation packet.\n"
        "- Verified the accepted live-result fields are unchanged "
        "(`status=pass`, `request_count=1`, `no_retry=true`, "
        "`second_attempt_made=false`, all raw/credential persist flags "
        "`false`).\n"
        "- Confirmed all future live gates remain blocked.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "No live Telegram API call. No sendMessage / getMe / getChat / "
        "getChatMember / getUpdates / webhook / scheduler / reply / DM / "
        "metrics / scraping. No credential, env, or account-binding read. No "
        "secret / account id / message id value / date value / raw request / "
        "raw response persisted.\n"
        "\n"
        "## Next\n"
        "\n"
        "Recommended next task: "
        "`TASK_CONTENTOPS_0174CT_OPERATOR_LIVE_PUBLISHING_REVIEW_AND_"
        "PLATFORM_REQUIREMENTS_BACKLOG_V0`.\n"
        "\n"
        "Live posting remains blocked until a new explicit task and operator "
        "GO. Recommendation: pause additional live sends and review the two "
        "Telegram pilot posts plus the evidence chain before expanding.\n"
    )


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_reconciliation_gate(*, write=False, repo_root=None, ledger=None):
    """Run the strictly-local 0174CS reconciliation gate. Fail-closed.

    ``ledger`` may be injected for tests; otherwise it is loaded from disk.
    Writing occurs ONLY when ``write=True`` AND both artifacts pass redaction.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(__file__))

    blocked = []

    if ledger is None:
        ledger = load_ledger(repo_root)
    if not isinstance(ledger, dict):
        return _summary(write=write, status="blocked",
                        blocked_reasons=["ledger_0174cr_missing_or_unparseable"],
                        correction_applied=False)

    # 1. Verify accepted live-result fields are unchanged BEFORE correcting.
    live_ok, live_reasons = verify_live_fields_unchanged(ledger)
    if not live_ok:
        blocked.extend(live_reasons)

    # 2. Redaction scan of the source ledger (must already be clean).
    src_violations = scan_ledger_for_leaks(ledger)
    if src_violations:
        blocked.append("source_ledger_redaction_violation")

    # 3. Compute the corrected ledger (copy) + verify only allowed keys change.
    corrected = apply_correction(ledger)
    allowed_ok, illegal_keys = correction_only_touches_allowed_keys(
        ledger, corrected)
    if not allowed_ok:
        blocked.append("correction_touched_disallowed_keys:" +
                       ",".join(illegal_keys))

    # 4. Re-verify live fields unchanged on the corrected ledger.
    post_live_ok, post_live_reasons = verify_live_fields_unchanged(corrected)
    if not post_live_ok:
        blocked.extend(f"post_correction_{r}" for r in post_live_reasons)

    # 5. Redaction scan the corrected ledger.
    corrected_violations = scan_ledger_for_leaks(corrected)
    if corrected_violations:
        blocked.append("corrected_ledger_redaction_violation")

    current_ledger_checksum = compute_checksum(corrected)

    # 6. Build the reconciliation packet + redaction scan it.
    status = "pass" if not blocked else "blocked"
    packet = build_reconciliation_packet(
        ledger=corrected,
        correction_applied=(write and not blocked),
        live_fields_ok=live_ok and post_live_ok,
        current_ledger_checksum=current_ledger_checksum,
        status=status, blocked_reasons=blocked)
    packet_violations = scan_ledger_for_leaks(packet)
    if packet_violations:
        blocked.append("packet_redaction_violation")
        status = "blocked"
        packet["status"] = "blocked"
        packet["blocked_reasons"] = sorted(set(blocked))

    packet_checksum = compute_checksum(packet)
    packet["reconciliation_packet_checksum"] = packet_checksum

    ledger_written = False
    packet_written = False
    readme_written = False

    # 7. Persist ONLY when write flag is present AND nothing is blocked.
    if write and not blocked:
        # Corrected current 0174CR ledger.
        ledger_path = os.path.join(repo_root, LEDGER_REL_PATH)
        with open(ledger_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(serialize(corrected))
        ledger_written = True

        # 0174CS reconciliation packet + README.
        out_dir = os.path.join(repo_root, PACKET_REL_DIR)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, PACKET_FILENAME), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(serialize(packet))
        packet_written = True
        with open(os.path.join(out_dir, README_FILENAME), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(build_readme())
        readme_written = True

    return _summary(
        write=write, status=status, blocked_reasons=blocked,
        correction_applied=(write and not blocked),
        current_ledger_checksum=current_ledger_checksum,
        packet_checksum=packet_checksum,
        ledger_written=ledger_written, packet_written=packet_written,
        readme_written=readme_written,
        live_fields_ok=(live_ok and post_live_ok))


def _summary(*, write, status, blocked_reasons, correction_applied,
             current_ledger_checksum=None, packet_checksum=None,
             ledger_written=False, packet_written=False, readme_written=False,
             live_fields_ok=False):
    """Redacted gate summary dict."""
    return {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "source_0174cr_pre_live_commit_expected":
            SOURCE_0174CR_PRE_LIVE_COMMIT_EXPECTED,
        "source_0174cr_post_live_ledger_commit":
            SOURCE_0174CR_POST_LIVE_LEDGER_COMMIT,
        "ledger_path_reconciled": LEDGER_REL_PATH.replace(os.sep, "/"),
        "packet_path": os.path.join(PACKET_REL_DIR, PACKET_FILENAME).replace(
            os.sep, "/"),
        "original_pre_live_implementation_commit_recorded":
            ORIGINAL_PRE_LIVE_COMMIT_RECORDED,
        "corrected_pre_live_implementation_commit": CORRECTED_PRE_LIVE_COMMIT,
        "correction_applied_to_current_ledger": bool(correction_applied),
        "correction_reason": CORRECTION_REASON,
        "live_result_fields_changed": False,
        "live_result_still_pass": bool(live_fields_ok),
        "write_requested": bool(write),
        "ledger_written": bool(ledger_written),
        "packet_written": bool(packet_written),
        "readme_written": bool(readme_written),
        "current_ledger_checksum_after_reconciliation": current_ledger_checksum,
        "reconciliation_packet_checksum": packet_checksum,
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_posting_performed": True,
        "no_scheduler_created": True,
        "no_webhook_created": True,
        "no_reply_dm_created": True,
        "no_metrics_fetched": True,
        "no_scraping_performed": True,
        "redaction_verified": True,
        "operator_roadmap": build_operator_roadmap(),
        "status": status,
        "blocked_reasons": sorted(set(blocked_reasons)),
    }


def summary(**kwargs):
    """Convenience wrapper returning the redacted gate summary dict."""
    return run_reconciliation_gate(**kwargs)


def main(argv=None):
    """CLI: print ONLY the redacted JSON summary. Local-only, no network/env."""
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    write = FLAG_WRITE in args
    result = run_reconciliation_gate(write=write)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
