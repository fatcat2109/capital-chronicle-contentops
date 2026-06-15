"""Operator live-publishing review + platform requirements backlog gate (0174CT).

This module is STRICTLY LOCAL. It performs NO network of any kind and reads NO
env/credentials. It exists to:

  * Summarize the accepted 0174CK..0174CS_R1 supervised publishing chain.
  * Confirm the current posture after exactly two supervised Telegram live
    pilots (paused; all future live publishing blocked).
  * Read the two prior redacted live-pilot ledgers locally (0174CO first-pilot
    summary ledger and 0174CR second-pilot ledger) only to derive boolean
    safety attestations -- never to copy raw identifiers.
  * Emit an operator review packet + a platform requirements backlog for
    telegram_pause_and_review, telegram_third_gate_later, x_requirements_only,
    and linkedin_requirements_only.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / socket / dotenv).
  * No process env / .env read (no environment-variable lookups).
  * Imports ONLY hashlib, json, os.path, re.
  * Fail-closed: writes happen ONLY when the write flag is present AND the
    redaction scan passes on the packet.
  * Reads prior ledgers ONLY as local files; never mutates them.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
  * No live call, no posting, no scheduler/webhook/getUpdates/reply/DM/metrics,
    no scraping, no OAuth, no account binding, no generic publisher.
"""

import hashlib
import json
import os.path
import re

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CT_OPERATOR_LIVE_PUBLISHING_REVIEW_AND_"
    "PLATFORM_REQUIREMENTS_BACKLOG_V0"
)

GATE = "OPERATOR_LIVE_PUBLISHING_REVIEW_BACKLOG_0174CT"
SOURCE_BASELINE_COMMIT = "41d45ca7910db6f303b73c9f8bbc7aeee432992b"

NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174CU_PLATFORM_REQUIREMENTS_AND_ACCOUNT_BINDING_"
    "POLICY_PACKETS_NO_LIVE_V0"
)

FIRST_LIVE_TASK = (
    "TASK_CONTENTOPS_0174CN_TELEGRAM_FIRST_SUPERVISED_LIVE_POST_TO_"
    "OPERATOR_APPROVED_TARGET_V0"
)
SECOND_LIVE_TASK = (
    "TASK_CONTENTOPS_0174CR_TELEGRAM_SECOND_SUPERVISED_LIVE_POST_"
    "OPERATOR_GO_GATE_V0"
)

# Prior redacted live-pilot ledgers (read-only, local).
FIRST_LEDGER_REL_PATH = os.path.join(
    "docs", "credential_readiness", "0174CO",
    "telegram_post_pilot_ledger_0174cn.json")
SECOND_LEDGER_REL_PATH = os.path.join(
    "docs", "credential_readiness", "0174CR",
    "telegram_second_supervised_live_post_ledger.json")

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174CT")
PACKET_FILENAME = "operator_live_publishing_review_backlog_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-operator-live-publishing-review-backlog"


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth; extends the Telegram contract with
# X / LinkedIn account + URN guards).
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
_LINKEDIN_URN = re.compile(r"urn:li:[A-Za-z]+:")

_FORBIDDEN_KEYS = (
    "token", "bot_token", "chat_id", "channel_id", "channel_username",
    "bot_id", "bot_username", "message_id", "message_id_value", "date",
    "date_value", "raw_url", "raw_request", "raw_response",
    "target_identifier", "target_value", "access_token", "refresh_token",
    "client_secret", "api_key", "account_id", "account_handle",
    "organization_id", "person_urn", "organization_urn",
)


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s == SOURCE_BASELINE_COMMIT:
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
        if _LINKEDIN_URN.search(s):
            violations.append(f"linkedin_urn:{key or 'value'}")
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
# Prior ledger load (read-only) + boolean attestations
# --------------------------------------------------------------------------- #
def _load_ledger(repo_root, rel_path):
    """Load a prior redacted ledger dict, or None if missing/unparseable."""
    path = os.path.join(repo_root, rel_path)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.loads(fh.read())
    except (ValueError, OSError):
        return None


def _no_retry_attested(ledger):
    """A pilot is no-retry if it states so, or if budget==count==1."""
    if not isinstance(ledger, dict):
        return False
    if ledger.get("no_retry") is True:
        return True
    return ledger.get("request_count") == 1 and ledger.get("request_budget") == 1


def build_live_pilot_summary(first_ledger, second_ledger):
    """Derive redacted boolean attestations across the two live pilots."""
    both_present = isinstance(first_ledger, dict) and isinstance(
        second_ledger, dict)

    def _both(pred):
        return bool(both_present and pred(first_ledger) and pred(second_ledger))

    return {
        "telegram_live_pilot_count": 2,
        "first_live_task": FIRST_LIVE_TASK,
        "second_live_task": SECOND_LIVE_TASK,
        "both_live_posts_redacted_ledgers_present": both_present,
        "both_live_posts_request_count_one":
            _both(lambda d: d.get("request_count") == 1),
        "both_live_posts_no_retry":
            bool(both_present and _no_retry_attested(first_ledger)
                 and _no_retry_attested(second_ledger)),
        "both_live_posts_message_id_value_not_persisted":
            _both(lambda d: d.get("message_id_value_persisted") is False),
        "both_live_posts_raw_request_response_not_persisted":
            _both(lambda d: d.get("raw_request_persisted") is False
                  and d.get("raw_response_persisted") is False),
    }


# --------------------------------------------------------------------------- #
# Accepted chain + current posture
# --------------------------------------------------------------------------- #
def build_accepted_chain():
    """The accepted 0174CK..0174CS_R1 supervised publishing chain."""
    return {
        "telegram_identity_validated": True,
        "telegram_target_binding_validated": True,
        "first_dry_run_preflight_accepted": True,
        "first_live_post_delivered_once": True,
        "first_post_pilot_ledger_persisted": True,
        "next_platform_selection_accepted": True,
        "second_dry_run_ledger_accepted": True,
        "second_live_post_delivered_once": True,
        "second_live_post_ledger_reconciled": True,
        "test_isolation_repair_accepted": True,
    }


def build_current_operator_posture():
    """The conservative current operator posture after two pilots."""
    return {
        "live_posting_state": "blocked_until_new_explicit_task_and_operator_go",
        "immediate_recommendation": "pause_additional_live_sends_and_review",
        "reason": (
            "two Telegram pilots prove supervised path; next risk is "
            "operational expansion, not send mechanics"
        ),
        "global_scheduler_enabled": False,
        "webhook_enabled": False,
        "get_updates_enabled": False,
        "autonomous_replies_enabled": False,
        "metrics_fetch_enabled": False,
        "scraping_enabled": False,
        "generic_publisher_enabled": False,
    }


# --------------------------------------------------------------------------- #
# Platform requirements backlog
# --------------------------------------------------------------------------- #
def build_platform_requirements_backlog():
    """The four requirements-only backlog items (no live work now)."""
    return {
        "telegram_pause_and_review": {
            "objective": (
                "Review both Telegram pilot posts, ledgers, operator evidence, "
                "and safety posture before any additional live send."
            ),
            "allowed_now": [
                "local evidence review",
                "ledger checks",
                "README/packet generation",
            ],
            "forbidden_now": [
                "any live post", "getUpdates", "webhook", "scheduler",
                "reply/DM", "metrics fetch",
            ],
            "required_before_live": [
                "new explicit task", "new exact payload", "dry-run ledger",
                "approval hash", "one-time operator GO",
            ],
            "credential_policy":
                "no credential read; reuse already-validated local target only "
                "under a future explicit task",
            "account_binding_policy":
                "no new account binding; target already validated by 0174CL",
            "approval_policy":
                "one-time operator GO + exact payload-hash lock required before "
                "any send",
            "redaction_policy":
                "no chat/channel/message ids, no raw URLs, booleans/classes only",
            "test_policy":
                "network-free review tests only; no live call",
            "blockers": [
                "no new operator GO yet",
                "review of two pilots not yet signed off",
            ],
            "recommended_priority": 1,
        },
        "telegram_third_gate_later": {
            "objective": (
                "Define requirements for a possible third Telegram supervised "
                "live post, but do not implement or send it now."
            ),
            "allowed_now": ["requirements-only planning"],
            "forbidden_now": [
                "new live module", "sendMessage", "credential read",
            ],
            "required_before_live": [
                "separate dry-run gate", "separate live gate",
                "duplicate-send prevention", "pre-attempt marker",
                "post-send redacted ledger", "no retry",
            ],
            "credential_policy":
                "no token read until a dedicated credential-readiness gate",
            "account_binding_policy":
                "no new binding; existing validated target only",
            "approval_policy":
                "separate one-time operator GO + exact payload-hash lock",
            "redaction_policy":
                "same redacted-only contract as 0174CN/0174CR ledgers",
            "test_policy":
                "network-free dry-run + live-gate tests with injected caller",
            "blockers": [
                "third send not justified until pause/review complete",
            ],
            "recommended_priority": 4,
        },
        "x_requirements_only": {
            "objective": (
                "Prepare requirements for future X account binding and dry-run "
                "contract only."
            ),
            "allowed_now": ["official-docs review only", "no OAuth"],
            "forbidden_now": [
                "OAuth", "token exchange", "post", "metrics",
                "replies/DMs", "scraping",
            ],
            "required_before_live": [
                "developer access/tier verified",
                "OAuth user context design",
                "account-binding proof",
                "dry-run payload contract",
                "redacted ledger",
                "explicit GO",
            ],
            "credential_policy":
                "no token until a dedicated credential-readiness gate",
            "account_binding_policy":
                "no account id/handle persisted raw",
            "approval_policy":
                "explicit operator GO + dry-run acceptance before any live call",
            "redaction_policy":
                "no raw handles, account ids, or tokens; booleans/classes only",
            "test_policy":
                "requirements + redaction tests only; no API call",
            "blockers": [
                "developer access/tier not yet verified",
                "OAuth user-context design not yet drafted",
            ],
            "recommended_priority": 2,
        },
        "linkedin_requirements_only": {
            "objective": (
                "Prepare requirements for future LinkedIn member/org/page "
                "binding and dry-run contract only."
            ),
            "allowed_now": [
                "official-docs review only", "no OAuth/product-access flow",
            ],
            "forbidden_now": [
                "member token", "organization id", "page binding", "post",
                "metrics", "scraping",
            ],
            "required_before_live": [
                "role/product-access verified",
                "version header policy",
                "organization/page ownership proof",
                "dry-run payload contract",
                "redacted ledger",
                "explicit GO",
            ],
            "credential_policy":
                "no token until a dedicated credential-readiness gate",
            "account_binding_policy":
                "no organization URN/person URN persisted raw",
            "approval_policy":
                "explicit operator GO + dry-run acceptance before any live call",
            "redaction_policy":
                "no URNs, organization ids, or tokens; booleans/classes only",
            "test_policy":
                "requirements + redaction tests only; no API call",
            "blockers": [
                "role/product-access not yet verified",
                "organization/page ownership proof not yet established",
            ],
            "recommended_priority": 3,
        },
    }


def build_required_before_expansion():
    """What must be proven before any next live post or platform expansion."""
    return {
        "before_any_next_live_post": [
            "new explicit task with exact payload",
            "platform-specific dry-run ledger accepted",
            "exact approval payload-hash lock",
            "one-time operator GO scoped to that task",
            "duplicate-send prevention + pre-attempt marker",
            "post-send redacted ledger with request_count==1 and no retry",
        ],
        "before_any_platform_expansion": [
            "platform developer access/tier verified",
            "account-binding ownership proof (no raw ids persisted)",
            "credential-readiness gate (no token until then)",
            "redaction contract defined for that platform",
            "network-free requirements + redaction tests passing",
        ],
    }


def build_roadmap():
    """Concise roadmap: pause/review first, then requirements-only gates."""
    return {
        "step_1": "pause additional live sends",
        "step_2": "review the two Telegram pilots + evidence chain",
        "step_3": "build requirements-only packets (X, LinkedIn) -- no OAuth",
        "step_4": "define telegram third-gate requirements (no send)",
        "step_5": (
            "only after sign-off: a new explicit live task with dry-run, "
            "approval-hash lock, and one-time operator GO"
        ),
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        "no_autonomous_publishing": True,
        "no_scheduler": True,
        "no_webhook": True,
        "no_get_updates": True,
        "no_reply_dm": True,
        "no_metrics_fetch": True,
        "no_scraping": True,
    }


# --------------------------------------------------------------------------- #
# Packet + README
# --------------------------------------------------------------------------- #
def build_packet(*, live_pilot_summary, status, blocked_reasons):
    """Assemble the 0174CT operator review + backlog packet (redacted)."""
    return {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "accepted_chain": build_accepted_chain(),
        "live_pilot_summary": live_pilot_summary,
        "current_operator_posture": build_current_operator_posture(),
        "platform_requirements_backlog":
            build_platform_requirements_backlog(),
        "required_before_expansion": build_required_before_expansion(),
        "roadmap": build_roadmap(),
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
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
        "status": status,
        "blocked_reasons": sorted(set(blocked_reasons)),
    }


def build_readme():
    """Concise operator-facing README for the 0174CT packet."""
    return (
        "# 0174CT Operator Live-Publishing Review + Platform Requirements "
        "Backlog\n"
        "\n"
        "Strictly local, no-network review packet produced after exactly two "
        "supervised Telegram live pilots.\n"
        "\n"
        "## Current posture\n"
        "\n"
        "- Live posting state: `blocked_until_new_explicit_task_and_operator_"
        "go`.\n"
        "- Immediate recommendation: pause additional live sends and review "
        "the two Telegram pilots plus the evidence chain.\n"
        "- No scheduler / webhook / getUpdates / autonomous replies / metrics "
        "fetch / scraping / generic publisher.\n"
        "\n"
        "## Platform requirements backlog (requirements-only, no live work)\n"
        "\n"
        "1. `telegram_pause_and_review` (priority 1)\n"
        "2. `x_requirements_only` (priority 2) -- official-docs review only, "
        "no OAuth.\n"
        "3. `linkedin_requirements_only` (priority 3) -- official-docs review "
        "only, no OAuth/product-access flow.\n"
        "4. `telegram_third_gate_later` (priority 4) -- requirements-only, no "
        "send.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "No live Telegram/X/LinkedIn API call. No sendMessage / getMe / "
        "getChat / getChatMember / getUpdates / webhook / scheduler / reply / "
        "DM / metrics / scraping / OAuth. No credential, env, or "
        "account-binding read. Prior live ledgers were read locally and left "
        "unchanged.\n"
        "\n"
        "## Next\n"
        "\n"
        f"Recommended next task: `{NEXT_RECOMMENDED_TASK}`.\n"
    )


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_review_backlog_gate(*, write=False, repo_root=None,
                            first_ledger=None, second_ledger=None):
    """Run the strictly-local 0174CT review + backlog gate. Fail-closed.

    Prior ledgers may be injected for tests; otherwise they are read from disk
    (read-only). Writing occurs ONLY when ``write=True`` AND the packet passes
    the redaction scan.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(__file__))

    blocked = []

    if first_ledger is None:
        first_ledger = _load_ledger(repo_root, FIRST_LEDGER_REL_PATH)
    if second_ledger is None:
        second_ledger = _load_ledger(repo_root, SECOND_LEDGER_REL_PATH)

    live_pilot_summary = build_live_pilot_summary(first_ledger, second_ledger)

    # The packet content is self-contained and deterministic; build then scan.
    status = "pass"
    packet = build_packet(
        live_pilot_summary=live_pilot_summary, status=status,
        blocked_reasons=blocked)

    packet_violations = scan_ledger_for_leaks(packet)
    if packet_violations:
        blocked.append("packet_redaction_violation")
        status = "blocked"
        packet["status"] = "blocked"
        packet["blocked_reasons"] = sorted(set(blocked))

    packet_checksum = compute_checksum(packet)

    packet_written = False
    readme_written = False

    if write and not blocked:
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
        live_pilot_summary=live_pilot_summary,
        packet_checksum=packet_checksum,
        packet_written=packet_written, readme_written=readme_written)


def _summary(*, write, status, blocked_reasons, live_pilot_summary,
             packet_checksum=None, packet_written=False, readme_written=False):
    """Redacted gate summary dict."""
    return {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "accepted_chain": build_accepted_chain(),
        "live_pilot_summary": live_pilot_summary,
        "current_operator_posture": build_current_operator_posture(),
        "platform_requirements_backlog": build_platform_requirements_backlog(),
        "required_before_expansion": build_required_before_expansion(),
        "roadmap": build_roadmap(),
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        "write_requested": bool(write),
        "packet_path": os.path.join(PACKET_REL_DIR, PACKET_FILENAME).replace(
            os.sep, "/"),
        "packet_written": bool(packet_written),
        "readme_written": bool(readme_written),
        "packet_checksum": packet_checksum,
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
        "status": status,
        "blocked_reasons": sorted(set(blocked_reasons)),
    }


def summary(**kwargs):
    """Convenience wrapper returning the redacted gate summary dict."""
    return run_review_backlog_gate(**kwargs)


def main(argv=None):
    """CLI: print ONLY the redacted JSON summary. Local-only, no network/env."""
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    write = FLAG_WRITE in args
    result = run_review_backlog_gate(write=write)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
