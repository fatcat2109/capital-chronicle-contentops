import pytest
from live_contentops import platform_variant_constraint_registry_v6 as registry

def test_registry_contains_all_required_families():
    required = [
        "substack_canonical",
        "discord_drop",
        "telegram_operator_post",
        "x_manual_thread",
        "linkedin_manual_post",
        "threads_manual_post",
        "facebook_manual_post",
        "instagram_manual_caption",
        "manual_fallback_export"
    ]
    for family in required:
        assert family in registry.PLATFORM_FAMILIES
        c = registry.get_constraints(family)
        assert c["platform_family"] == family
        assert c["live_api_supported_now"] is False
        assert c["dispatch_supported_now"] is False
        assert c["public_postable"] is False
        assert c["account_binding_required_before_live"] is True
        assert c["approval_required"] is True
        assert c["exact_payload_hash_required"] is True
        assert c["manual_fallback_available"] is True
        assert c["official_docs_required_before_live"] is True
        assert isinstance(c["max_text_length"], int)

def test_invalid_family_raises_key_error():
    with pytest.raises(KeyError):
        registry.get_constraints("invalid_family")
