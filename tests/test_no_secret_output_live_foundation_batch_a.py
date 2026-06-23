import pytest

from live_contentops.credential_redaction_policy import assert_no_secret_shaped_text, contains_secret_shaped_text, redact_text


def test_secret_shaped_strings_fail_closed():
    secret = "TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
    assert contains_secret_shaped_text(secret)
    with pytest.raises(ValueError):
        assert_no_secret_shaped_text(secret)


def test_redaction_removes_secret_without_prefix_suffix_digest():
    secret = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890"
    redacted = redact_text(secret)
    assert "abcdefghijklmnopqrstuvwxyz" not in redacted
    assert "1234567890" not in redacted
    assert "[REDACTED_SECRET_SHAPED_TEXT]" in redacted
