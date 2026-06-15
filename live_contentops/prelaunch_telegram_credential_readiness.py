"""Pre-launch Telegram credential readiness harness (0174CJ).

This module answers a narrow pre-launch question: is the repo-local environment
*shaped* such that a FUTURE, separately-gated Telegram live validation task could
proceed? It is explicitly authorized to read a repo-local ``.env`` / ``.env.local``
source (or, only when explicitly selected, the process environment) to perform
presence + redacted shape classification for the Telegram credential slots.

HARD GUARANTEES (enforced by tests + leakage guards):
  * It NEVER prints, logs, persists, commits, or returns the raw token / chat id.
  * It NEVER reports a token/chat-id prefix, suffix, length, or hash/digest.
  * It NEVER reports an absolute or relative filesystem path; only redacted labels.
  * It NEVER calls the Telegram Bot API. It imports NO network / provider /
    platform / SDK libraries (only ``os``, ``re``, ``json``, ``datetime``).
  * Credential readiness here implies NO network / posting / scheduler permission.
    Presence/shape readiness and live API validation are SEPARATE gates.

Output is a flat, redacted, JSON-serializable summary (see ``REDACTED_FIELDS``).
"""

import json
import os
import re

TASK_LABEL = "TASK_CONTENTOPS_0174CJ_PRELAUNCH_TELEGRAM_CREDENTIAL_READINESS_DRY_RUN_AND_REDACTION_HARNESS_V0"
CHECK_MODE = "local_redacted_credential_readiness_check_only"
CANDIDATE_PLATFORM_ID = "telegram"

# Only these env keys are ever inspected. All other keys (names AND values) are
# silently ignored and never recorded anywhere.
APPROVED_SLOT_KEYS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_TARGET_CHAT_ID")

# Redacted source labels only. A real path must never appear here or anywhere.
SOURCE_LABEL_DOTENV = "REPO_LOCAL_DOTENV_REDACTED"
SOURCE_LABEL_DOTENV_LOCAL = "REPO_LOCAL_DOTENV_LOCAL_REDACTED"
SOURCE_LABEL_PROCESS_ENV = "PROCESS_ENV_SELECTED_REDACTED"
SOURCE_LABEL_PROVIDED = "OPERATOR_LOCAL_ENV_TEXT_PROVIDED_REDACTED"
SOURCE_LABEL_UNAVAILABLE = "unavailable"

_VALID_SOURCE_LABELS = (
    SOURCE_LABEL_DOTENV,
    SOURCE_LABEL_DOTENV_LOCAL,
    SOURCE_LABEL_PROCESS_ENV,
    SOURCE_LABEL_PROVIDED,
    SOURCE_LABEL_UNAVAILABLE,
)

# Token shape classes
TOKEN_ABSENT = "absent"
TOKEN_LIKE = "present_redacted_telegram_bot_token_like"
TOKEN_EMPTY = "present_redacted_empty_or_whitespace"
TOKEN_NONCLASSIFIABLE = "present_redacted_nonempty_nonclassifiable"

# Chat id shape classes
CHAT_ABSENT = "absent"
CHAT_INTEGER = "present_redacted_integer_like"
CHAT_HANDLE = "present_redacted_channel_handle_like"
CHAT_EMPTY = "present_redacted_empty_or_whitespace"
CHAT_NONCLASSIFIABLE = "present_redacted_nonempty_nonclassifiable"

# Readiness statuses
STATUS_BLOCKED_NO_SOURCE = "blocked_missing_env_source"
STATUS_BLOCKED_MISSING_SLOT = "blocked_missing_required_slot"
STATUS_REVIEW_SHAPE = "review_shape_nonclassifiable"
STATUS_READY = "ready_for_future_live_gate_validation"

# --- redacted shape classification (no values, lengths, snippets, hashes) ----

_BOT_TOKEN_LIKE = re.compile(r"^\d{6,}:[A-Za-z0-9_-]{30,}$")
_INTEGER_LIKE = re.compile(r"^-?\d+$")
_CHANNEL_HANDLE_LIKE = re.compile(r"^@[A-Za-z0-9_]{3,}$")


def classify_token_shape(raw):
    """Redacted shape class for a token value. Never returns/derives the value."""
    if raw is None:
        return TOKEN_ABSENT
    if raw.strip() == "":
        return TOKEN_EMPTY
    if _BOT_TOKEN_LIKE.match(raw.strip()):
        return TOKEN_LIKE
    return TOKEN_NONCLASSIFIABLE


def classify_chat_id_shape(raw):
    """Redacted shape class for a chat id value. Never returns/derives the value."""
    if raw is None:
        return CHAT_ABSENT
    s = raw.strip()
    if s == "":
        return CHAT_EMPTY
    if _INTEGER_LIKE.match(s):
        return CHAT_INTEGER
    if _CHANNEL_HANDLE_LIKE.match(s):
        return CHAT_HANDLE
    return CHAT_NONCLASSIFIABLE


def _is_present(raw):
    """A slot counts as present only if non-empty after strip."""
    return raw is not None and raw.strip() != ""


# --- env parsing (approved slots only, never records other keys/values) ------

def parse_approved_env_text(text):
    """Parse env text, returning ONLY approved slot raw values.

    Other keys, key names, and line contents are never returned or recorded.
    """
    values = {k: None for k in APPROVED_SLOT_KEYS}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, val = stripped.partition("=")
        key = key.strip()
        if key in APPROVED_SLOT_KEYS:
            v = val.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
                v = v[1:-1]
            values[key] = v
        # all other keys silently ignored
    return values


# --- leakage guard -----------------------------------------------------------

_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),       # telegram bot token body
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-100\d{8,}"),                        # realistic supergroup chat id
]


def _scan_secret_like(obj):
    """Return labels for any secret-like value appearing anywhere in the output."""
    errors = []

    def _walk(o, key=None):
        if isinstance(o, str):
            for pat in _SECRET_LIKE:
                if pat.search(o):
                    errors.append(f"secret_like_value_detected:{key or 'value'}")
                    break
        elif isinstance(o, dict):
            for k, v in o.items():
                _walk(v, k)
        elif isinstance(o, list):
            for v in o:
                _walk(v, key)

    _walk(obj)
    return errors


# --- readiness determination -------------------------------------------------

def _determine_readiness(env_available, token_present, token_class, chat_present, chat_class):
    if not env_available:
        return STATUS_BLOCKED_NO_SOURCE
    if not token_present or not chat_present:
        return STATUS_BLOCKED_MISSING_SLOT
    if token_class == TOKEN_LIKE and chat_class == CHAT_INTEGER:
        return STATUS_READY
    return STATUS_REVIEW_SHAPE


def _base_summary():
    return {
        "task_label": TASK_LABEL,
        "check_mode": CHECK_MODE,
        "candidate_platform_id": CANDIDATE_PLATFORM_ID,
        "env_source_read_attempted": False,
        "env_source_read_succeeded": False,
        "env_source_missing_or_unavailable": True,
        "env_source_label": SOURCE_LABEL_UNAVAILABLE,
        "telegram_bot_token_present": None,
        "telegram_bot_token_shape_class": TOKEN_ABSENT,
        "telegram_target_chat_id_present": None,
        "telegram_target_chat_id_shape_class": CHAT_ABSENT,
        "readiness_status": STATUS_BLOCKED_NO_SOURCE,
        # Hard-locked policy flags — never true for this harness.
        "live_api_allowed_now": False,
        "telegram_api_called": False,
        "live_posting_allowed_now": False,
        "scheduler_allowed_now": False,
        "credential_values_printed": False,
        "token_snippet_reported": False,
        "chat_id_snippet_reported": False,
        "exact_length_reported": False,
        "hash_or_digest_reported": False,
        "raw_path_reported": False,
        # Required-true flags.
        "manual_review_required": True,
        "future_live_gate_required": True,
    }


def build_readiness(*, env_text=None, env_available=None, source_label=None):
    """Build a redacted readiness summary from optional env text.

    env_text: raw text of an approved local env source supplied by the caller.
              Never logged, stored, or returned. If None and env_available is
              not True, the source is treated as unavailable (BLOCKED).
    env_available: explicit availability override. Defaults to (env_text is not None).
    source_label: redacted label only. A real path must never be passed here.
    """
    summary = _base_summary()

    if env_available is None:
        env_available = env_text is not None

    if source_label in _VALID_SOURCE_LABELS and source_label != SOURCE_LABEL_UNAVAILABLE:
        summary["env_source_label"] = source_label
    elif env_available:
        summary["env_source_label"] = SOURCE_LABEL_PROVIDED
    else:
        summary["env_source_label"] = SOURCE_LABEL_UNAVAILABLE

    summary["env_source_read_attempted"] = bool(env_available)

    if not env_available or env_text is None:
        summary["env_source_read_succeeded"] = False
        summary["env_source_missing_or_unavailable"] = True
        summary["telegram_bot_token_present"] = None
        summary["telegram_target_chat_id_present"] = None
        summary["telegram_bot_token_shape_class"] = TOKEN_ABSENT
        summary["telegram_target_chat_id_shape_class"] = CHAT_ABSENT
        summary["readiness_status"] = STATUS_BLOCKED_NO_SOURCE
        return summary

    parsed = parse_approved_env_text(env_text)
    token_raw = parsed["TELEGRAM_BOT_TOKEN"]
    chat_raw = parsed["TELEGRAM_TARGET_CHAT_ID"]

    token_present = _is_present(token_raw)
    chat_present = _is_present(chat_raw)
    token_class = classify_token_shape(token_raw)
    chat_class = classify_chat_id_shape(chat_raw)

    summary["env_source_read_succeeded"] = True
    summary["env_source_missing_or_unavailable"] = False
    summary["telegram_bot_token_present"] = token_present
    summary["telegram_target_chat_id_present"] = chat_present
    summary["telegram_bot_token_shape_class"] = token_class
    summary["telegram_target_chat_id_shape_class"] = chat_class
    summary["readiness_status"] = _determine_readiness(
        True, token_present, token_class, chat_present, chat_class
    )

    # Defensive redaction guard: if anything secret-like survived into the
    # output, fail closed to BLOCKED and drop the shape classes.
    if _scan_secret_like(summary):
        summary["telegram_bot_token_shape_class"] = TOKEN_NONCLASSIFIABLE
        summary["telegram_target_chat_id_shape_class"] = CHAT_NONCLASSIFIABLE
        summary["readiness_status"] = STATUS_REVIEW_SHAPE

    return summary


# --- env source reading (file / process env) ---------------------------------

def _read_repo_env_source(repo_root, use_process_env=False):
    """Read an approved local env source. Returns (env_text, source_label, available).

    Reads repo-root ``.env`` then ``.env.local``. If ``use_process_env`` is True
    and neither file exists, builds env_text from the approved process-env slots
    only. NEVER returns or records a filesystem path.
    """
    candidates = [
        (os.path.join(repo_root, ".env"), SOURCE_LABEL_DOTENV),
        (os.path.join(repo_root, ".env.local"), SOURCE_LABEL_DOTENV_LOCAL),
    ]
    for path, label in candidates:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read(), label, True

    if use_process_env:
        lines = []
        present_any = False
        for key in APPROVED_SLOT_KEYS:
            val = os.environ.get(key)
            if val is not None:
                lines.append(f"{key}={val}")
                present_any = True
        if present_any:
            return "\n".join(lines), SOURCE_LABEL_PROCESS_ENV, True

    return None, SOURCE_LABEL_UNAVAILABLE, False


def run_readiness_check(repo_root=None, use_process_env=False):
    """Read the approved local env source and return a redacted readiness summary.

    repo_root: directory to look for ``.env`` / ``.env.local``. Defaults to the
               repository root (parent of this package). Tests pass a temp dir.
    use_process_env: when True, fall back to the approved process-env slots if no
                     local env file is found. Off by default.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(__file__))

    env_text, source_label, available = _read_repo_env_source(
        repo_root, use_process_env=use_process_env
    )
    return build_readiness(
        env_text=env_text, env_available=available, source_label=source_label
    )


def summary(repo_root=None, use_process_env=False):
    """Convenience wrapper returning the redacted readiness summary dict."""
    return run_readiness_check(repo_root=repo_root, use_process_env=use_process_env)


def main(argv=None):
    """CLI: print ONLY the redacted JSON summary.

    Usage:
      python -m live_contentops.prelaunch_telegram_credential_readiness
      python -m live_contentops.prelaunch_telegram_credential_readiness --process-env
    """
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    use_process_env = "--process-env" in args
    result = run_readiness_check(use_process_env=use_process_env)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
