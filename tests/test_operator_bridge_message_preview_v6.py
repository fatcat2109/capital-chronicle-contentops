from live_contentops import operator_bridge_message_preview_v6 as preview

def test_discord_preview_fields():
    status = {
        "unified_payload_bundle_hash": "a" * 64,
        "platform_families": ["discord_drop", "telegram_operator_post"],
        "unified_payload_status": "READY_FOR_REVIEW_ONLY_HASHED_PAYLOADS",
        "blockers": ["source_verification_required"]
    }
    dp = preview.generate_discord_preview(status)
    assert dp["review_only"] is True
    assert "ContentOps V6 Operator Status" in dp["content_body"]
    assert "source_verification_required" in dp["content_body"]
    
    # Assert validation detects forbidden elements
    assert "secret_or_destination_material_detected" in preview.validate_preview_content("discord.com/api/webhooks/123")
    assert "executable_dispatch_control_detected" in preview.validate_preview_content("/dispatch trigger")
    assert "unexpected_live_status_claim" in preview.validate_preview_content("live_write_allowed_now=true")
