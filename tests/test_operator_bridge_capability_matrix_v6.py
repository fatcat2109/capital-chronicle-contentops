from live_contentops import operator_bridge_capability_matrix_v6 as cm

def test_capability_matrix_properties():
    matrix = cm.generate_capability_matrix()
    
    # Assert Discord Webhook capability
    discord_row = next(r for r in matrix if r["platform_family"] == "discord_webhook")
    assert discord_row["live_enabled"] is False
    assert discord_row["credential_present"] == "unknown_not_checked"
    assert discord_row["official_docs_required_before_live"] is True
    assert discord_row["account_binding_required_before_live"] is True
    assert discord_row["manual_fallback_available"] is True
    assert discord_row["current_result"] == "review_only_preview"
