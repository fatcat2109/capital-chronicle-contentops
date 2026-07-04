import json

from live_contentops import discord_environment_contract as env_contract
from live_contentops import discord_webhook_payload_contract as payload_contract


def make_payload(payload_type: str, **overrides):
    kwargs = {
        "payload_id": f"test_{payload_type}",
        "payload_type": payload_type,
        "title": "Safe editorial update",
        "body": "Research workflow update for operator review.",
        "disclosure": "Educational content only. Not investment, legal, tax, or personal finance guidance.",
    }
    if payload_type == "substack_drop":
        kwargs["discussion_question"] = "What topic should be expanded next?"
    kwargs.update(overrides)
    return payload_contract.build_payload(**kwargs)


def rendered_text(payload):
    return json.dumps(payload_contract.render_dry_run(payload), sort_keys=True)


def test_all_six_payload_types_validate():
    for payload_type in payload_contract.PAYLOAD_TARGETS:
        payload = make_payload(payload_type)
        assert payload.validation_status == "valid"
        assert payload.blockers == ()
        assert payload.dry_run_only is True
        assert payload.live_write_allowed_now is False


def test_substack_drop_requires_discussion_question():
    payload = payload_contract.build_payload(
        payload_id="missing_question",
        payload_type="substack_drop",
        title="Safe title",
        body="Safe body",
        disclosure="Educational content only.",
    )
    assert payload.validation_status == "blocked"
    assert "substack_drop_requires_discussion_question" in payload.blockers


def test_announcement_and_product_update_render_without_discussion_question():
    for payload_type in ("announcement", "product_update"):
        payload = make_payload(payload_type, discussion_question=None)
        rendered = payload_contract.render_dry_run(payload)
        assert payload.validation_status == "valid"
        assert rendered["discussion_question"] is None
        assert "not_required" in rendered["human_readable_preview"]


def test_operator_private_payload_types_route_to_operator_private_binding():
    for payload_type in ("operator_private_summary", "manual_fallback_notice", "audit_summary_redacted"):
        payload = make_payload(payload_type)
        assert payload.target_name == "operator_private"
        assert payload.destination_binding_id == env_contract.OPERATOR_BINDING_ID
        assert payload.credential_handle_id == payload_contract.OPERATOR_CREDENTIAL_HANDLE_ID


def test_finance_trading_language_is_blocked():
    payload = make_payload("announcement", body="This is a buy trading signal with a price target.")
    assert "unsafe_finance_trading_language" in payload.blockers


def test_webhook_url_like_string_is_blocked():
    payload = make_payload("announcement", body="Do not show https://discord.com/api/webhooks/123/abc")
    assert "webhook_url_like_value" in payload.blockers


def test_raw_secret_like_string_is_blocked():
    payload = make_payload("announcement", body="Provider key sk-abcdefghijklmnopqrstuvwxyz123456")
    assert "raw_secret_like_value" in payload.blockers


def test_cookie_session_localstorage_selfbot_wording_is_blocked():
    for word in ("cookie", "session", "localStorage", "selfbot", "Discord user token"):
        payload = make_payload("announcement", body=f"Unsafe wording: {word}")
        assert "cookie_session_local_storage_or_selfbot" in payload.blockers


def test_unapproved_live_write_and_dispatch_claims_blocked():
    for phrase in ("live write enabled", "webhook sent", "sent to Discord", "dispatch happened"):
        payload = make_payload("announcement", body=f"Unsafe claim: {phrase}")
        assert "unapproved_live_write_or_dispatch_claim" in payload.blockers


def test_scheduler_and_engagement_automation_language_blocked():
    for phrase, blocker in (
        ("hidden scheduler", "hidden_scheduler_or_autonomous_posting"),
        ("autonomous posting", "hidden_scheduler_or_autonomous_posting"),
        ("auto reply", "dm_reply_engagement_automation"),
        ("DM automation", "dm_reply_engagement_automation"),
    ):
        payload = make_payload("announcement", body=f"Unsafe phrase: {phrase}")
        assert blocker in payload.blockers


def test_renderer_emits_no_webhook_url_or_token_metadata():
    payload = make_payload("announcement")
    rendered = payload_contract.render_dry_run(payload)
    text = json.dumps(rendered, sort_keys=True).lower()
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert "token_value" not in text
    assert rendered["secret_output_policy"]["token_metadata_output"] is False


def test_renderer_keeps_live_write_allowed_false():
    rendered = payload_contract.render_dry_run(make_payload("announcement"))
    assert rendered["dry_run_only"] is True
    assert rendered["live_write_allowed_now"] is False


def test_payloads_map_to_discord_environment_contract_binding_ids():
    catalog = payload_contract.target_binding_catalog()
    destinations = {item.target_name: item for item in env_contract.WEBHOOK_DESTINATIONS}
    assert catalog["announcements"]["destination_binding_id"] == destinations["announcements"].destination_binding_id
    assert catalog["substack_drops"]["destination_binding_id"] == destinations["substack_drops"].destination_binding_id
    assert catalog["product_updates"]["destination_binding_id"] == destinations["product_updates"].destination_binding_id
    assert catalog["operator_private"]["destination_binding_id"] == env_contract.OPERATOR_BINDING_ID


def test_discord_bot_remains_unnecessary():
    packet = payload_contract.write_sample_payloads("docs/automation/DISCORD_WEBHOOK_PAYLOAD_CONTRACT/sample_payloads.json")
    assert packet["discord_bot_required"] is False
    assert all(item["live_write_allowed_now"] is False for item in packet["payloads"])
