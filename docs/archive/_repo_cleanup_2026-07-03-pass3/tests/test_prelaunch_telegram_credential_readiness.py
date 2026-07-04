import json
import os

import live_contentops.prelaunch_telegram_credential_readiness as readiness

# Clearly-fake synthetic values. NOT real credentials. Used only to exercise
# classification/presence logic; they must never leak into emitted output.
FAKE_TOKEN = "111111:FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE_xx"
FAKE_CHAT_ID = "-1009999999999"
FAKE_HANDLE = "@fake_test_channel"


def _write_env(tmp_path, body):
    p = tmp_path / ".env"
    p.write_text(body, encoding="utf-8")
    return str(tmp_path)


# --- readiness status outcomes ----------------------------------------------

def test_token_like_and_integer_chat_is_ready(tmp_path):
    root = _write_env(
        tmp_path,
        f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n",
    )
    s = readiness.summary(repo_root=root)
    assert s["readiness_status"] == "ready_for_future_live_gate_validation"
    assert s["telegram_bot_token_present"] is True
    assert s["telegram_target_chat_id_present"] is True
    assert s["telegram_bot_token_shape_class"] == "present_redacted_telegram_bot_token_like"
    assert s["telegram_target_chat_id_shape_class"] == "present_redacted_integer_like"
    assert s["env_source_read_succeeded"] is True
    assert s["env_source_label"] == "REPO_LOCAL_DOTENV_REDACTED"


def test_token_like_and_channel_handle_is_review(tmp_path):
    root = _write_env(
        tmp_path,
        f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={FAKE_HANDLE}\n",
    )
    s = readiness.summary(repo_root=root)
    assert s["telegram_target_chat_id_shape_class"] == "present_redacted_channel_handle_like"
    assert s["readiness_status"] == "review_shape_nonclassifiable"
    blob = json.dumps(s)
    assert FAKE_TOKEN not in blob
    assert FAKE_HANDLE not in blob


def test_missing_token_blocks(tmp_path):
    root = _write_env(tmp_path, f"TELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n")
    s = readiness.summary(repo_root=root)
    assert s["telegram_bot_token_present"] is False
    assert s["telegram_bot_token_shape_class"] == "absent"
    assert s["readiness_status"] == "blocked_missing_required_slot"


def test_missing_chat_id_blocks(tmp_path):
    root = _write_env(tmp_path, f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\n")
    s = readiness.summary(repo_root=root)
    assert s["telegram_target_chat_id_present"] is False
    assert s["telegram_target_chat_id_shape_class"] == "absent"
    assert s["readiness_status"] == "blocked_missing_required_slot"


def test_malformed_token_is_review(tmp_path):
    root = _write_env(
        tmp_path,
        f"TELEGRAM_BOT_TOKEN=not-a-real-token\nTELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n",
    )
    s = readiness.summary(repo_root=root)
    assert s["telegram_bot_token_shape_class"] == "present_redacted_nonempty_nonclassifiable"
    assert s["readiness_status"] == "review_shape_nonclassifiable"


def test_whitespace_values_classified_safely(tmp_path):
    root = _write_env(
        tmp_path,
        "TELEGRAM_BOT_TOKEN=   \nTELEGRAM_TARGET_CHAT_ID=\n",
    )
    s = readiness.summary(repo_root=root)
    assert s["telegram_bot_token_present"] is False
    assert s["telegram_target_chat_id_present"] is False
    assert s["telegram_bot_token_shape_class"] == "present_redacted_empty_or_whitespace"
    assert s["telegram_target_chat_id_shape_class"] == "present_redacted_empty_or_whitespace"
    assert s["readiness_status"] == "blocked_missing_required_slot"


def test_missing_env_source_blocks(tmp_path):
    # tmp_path has no .env / .env.local
    s = readiness.summary(repo_root=str(tmp_path))
    assert s["readiness_status"] == "blocked_missing_env_source"
    assert s["env_source_missing_or_unavailable"] is True
    assert s["env_source_read_succeeded"] is False
    assert s["telegram_bot_token_present"] is None
    assert s["telegram_target_chat_id_present"] is None
    assert s["env_source_label"] == "unavailable"


# --- redaction / no-leak guarantees -----------------------------------------

def test_extra_unknown_keys_ignored_and_not_emitted(tmp_path):
    root = _write_env(
        tmp_path,
        (
            "OPENAI_API_KEY=should_be_ignored\n"
            "SOME_OTHER=zzz\n"
            f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\n"
            f"TELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n"
        ),
    )
    s = readiness.summary(repo_root=root)
    blob = json.dumps(s)
    assert "OPENAI_API_KEY" not in blob
    assert "SOME_OTHER" not in blob
    assert "should_be_ignored" not in blob
    assert "zzz" not in blob


def test_raw_secret_never_appears_in_output(tmp_path):
    root = _write_env(
        tmp_path,
        f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n",
    )
    s = readiness.summary(repo_root=root)
    blob = json.dumps(s)
    assert FAKE_TOKEN not in blob
    assert FAKE_CHAT_ID not in blob


def test_no_prefix_suffix_length_or_digest_emitted(tmp_path):
    root = _write_env(
        tmp_path,
        f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n",
    )
    s = readiness.summary(repo_root=root)
    blob = json.dumps(s)
    # No token prefix/suffix fragments.
    assert "111111" not in blob
    assert "FAKEFAKE" not in blob
    assert "_xx" not in blob
    # No chat id fragments.
    assert "9999999999" not in blob
    # No length / digest reporting.
    assert s["exact_length_reported"] is False
    assert s["hash_or_digest_reported"] is False
    assert s["token_snippet_reported"] is False
    assert s["chat_id_snippet_reported"] is False
    # No length integers for the secrets anywhere.
    assert str(len(FAKE_TOKEN)) not in blob
    assert str(len(FAKE_CHAT_ID)) not in blob


def test_no_filesystem_path_emitted(tmp_path):
    root = _write_env(
        tmp_path,
        f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n",
    )
    s = readiness.summary(repo_root=root)
    blob = json.dumps(s)
    assert str(tmp_path) not in blob
    assert ".env" not in blob
    assert s["raw_path_reported"] is False


def test_policy_flags_are_locked(tmp_path):
    root = _write_env(
        tmp_path,
        f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n",
    )
    s = readiness.summary(repo_root=root)
    assert s["live_api_allowed_now"] is False
    assert s["telegram_api_called"] is False
    assert s["live_posting_allowed_now"] is False
    assert s["scheduler_allowed_now"] is False
    assert s["credential_values_printed"] is False
    assert s["manual_review_required"] is True
    assert s["future_live_gate_required"] is True


def test_secret_scanner_rejects_leaked_value():
    # A leaked token-like value anywhere in the output is detected.
    leaked = {"x": "123456:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789xx"}
    assert readiness._scan_secret_like(leaked)
    # Clean redacted summary has no detections.
    clean = readiness._base_summary()
    assert readiness._scan_secret_like(clean) == []


# --- harness purity guarantees ----------------------------------------------

def test_no_network_provider_platform_imports_in_module():
    here = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(
        here, "live_contentops", "prelaunch_telegram_credential_readiness.py"
    )
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    for forbidden in (
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import openai",
        "import anthropic",
        "import tweepy",
        "import selenium",
        "import playwright",
        "telegram.org",
        "sendMessage",
        "getMe",
    ):
        assert forbidden not in src, f"forbidden token in readiness module: {forbidden}"


def test_provided_env_text_path_does_not_emit_path(tmp_path):
    # build_readiness with caller-supplied text + redacted label only.
    s = readiness.build_readiness(
        env_text=f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n",
        source_label="OPERATOR_LOCAL_ENV_TEXT_PROVIDED_REDACTED",
    )
    assert s["env_source_label"] == "OPERATOR_LOCAL_ENV_TEXT_PROVIDED_REDACTED"
    assert s["readiness_status"] == "ready_for_future_live_gate_validation"
