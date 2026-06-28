"""Test feedback snapshot redaction rules and blockers."""
from __future__ import annotations

from live_contentops import feedback_snapshot_redaction_v6 as redaction


def test_redact_text_safe():
    text = "Hello, this is a completely safe message asking about yields."
    redacted, blockers = redaction.redact_text(text)
    assert redacted == text
    assert len(blockers) == 0


def test_redact_text_email():
    text = "Contact me at jim@capitalchronicle.com to discuss."
    redacted, blockers = redaction.redact_text(text)
    assert "[EMAIL_REDACTED]" in redacted
    assert "jim@capitalchronicle.com" not in redacted
    assert "private_identifier_detected" in blockers
    assert "unredacted_personal_data_detected" in blockers


def test_redact_text_phone():
    text = "Call me at +1 555-0199."
    redacted, blockers = redaction.redact_text(text)
    assert "[PHONE_REDACTED]" in redacted
    assert "555-0199" not in redacted
    assert "private_identifier_detected" in blockers
    assert "unredacted_personal_data_detected" in blockers


def test_redact_text_discord_id():
    text = "My Discord user ID is <@123456789012345678>."
    redacted, blockers = redaction.redact_text(text)
    assert "[DISCORD_ID_REDACTED]" in redacted
    assert "123456789012345678" not in redacted
    assert "private_identifier_detected" in blockers
    assert "secret_or_destination_material_detected" in blockers


def test_redact_text_secrets_and_tokens():
    text = "Here is my secret webhook URL: https://discord.com/api/webhooks/abc123xyz"
    redacted, blockers = redaction.redact_text(text)
    assert "[WEBHOOK_REDACTED]" in redacted
    assert "secret_or_destination_material_detected" in blockers


def test_redact_text_private_dms():
    text = "Can you send that to me in a private DM?"
    redacted, blockers = redaction.redact_text(text)
    assert "dm_or_private_message_detected" in blockers


def test_redact_snapshot_fake_url_and_metrics():
    snap = {
        "snapshot_id": "snap_test",
        "raw_feedback_text_redacted": "Safe text",
        "author_handle_redacted": "user1",
        "public_url_verified": True,
        "metrics_verified": True,
        "metrics_optional": {"likes": 100},
        "contains_personal_data": False,
        "redaction_required": False,
        "blocked_reasons": []
    }
    redacted_snap, blockers = redaction.redact_snapshot(snap)
    assert redacted_snap["public_url_verified"] is False
    assert redacted_snap["metrics_verified"] is False
    assert "creates_fake_public_url" in blockers
    assert "claims_metrics_verified_without_evidence" in blockers


def test_redact_private_name_markers():
    # Handle check
    snap = {
        "snapshot_id": "snap_test_name",
        "raw_feedback_text_redacted": "Hello world",
        "author_handle_redacted": "user_delta_real_name_john_smith",
        "contains_personal_data": True,
        "redaction_required": True,
        "blocked_reasons": []
    }
    redacted_snap, blockers = redaction.redact_snapshot(snap)
    assert redacted_snap["author_handle_redacted"] == "[PRIVATE_NAME_REDACTED]"
    assert "private_name_marker_detected" in blockers
    assert "private_identifier_detected" in blockers

    # Text check
    text = "The user full_name is first_last."
    redacted, text_blockers = redaction.redact_text(text)
    assert "[PRIVATE_NAME_REDACTED]" in redacted
    assert "full_name" not in redacted.lower()
    assert "first_last" not in redacted.lower()
    assert "private_name_marker_detected" in text_blockers
    assert "private_identifier_detected" in text_blockers

