import json
from pathlib import Path

from live_contentops import discord_environment_contract as discord_contract
from live_contentops import v6_platform_registry_contract as registry_contract
from live_contentops.unified_credential_capability_matrix import build_matrix


def write_env(tmp_path: Path, text: str) -> Path:
    env_file = tmp_path / ".env"
    env_file.write_text(text, encoding="utf-8")
    return env_file


def row(packet: dict, platform_id: str) -> dict:
    return next(item for item in packet["platforms"] if item["platform_id"] == platform_id)


def test_discord_contract_builds_from_redacted_capability_matrix_without_values(tmp_path: Path):
    env_file = write_env(
        tmp_path,
        "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL=https://example.invalid/a\n"
        "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL=https://example.invalid/b\n"
        "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL=https://example.invalid/c\n"
        "DISCORD_SERVER_ID=raw-server-secret-value\n"
        "DISCORD_ANNOUNCEMENTS_CHANNEL_ID=raw-ann-secret-value\n"
        "DISCORD_OPERATOR_QUEUE_CHANNEL_ID=raw-ops-secret-value\n"
        "DISCORD_ROLE_FOUNDER=raw-founder-secret-value\n",
    )
    matrix_packet = build_matrix([env_file])
    packet = discord_contract.build_contract(matrix_packet)
    rendered = json.dumps(packet, sort_keys=True)
    assert packet["capability_class"] == "ready_webhook"
    assert packet["live_write_eligible"] is True
    assert packet["live_write_allowed_now"] is False
    assert "https://example.invalid" not in rendered
    assert "raw-server-secret-value" not in rendered
    assert "raw-ann-secret-value" not in rendered
    assert "raw-ops-secret-value" not in rendered
    assert "raw-founder-secret-value" not in rendered


def test_three_webhook_destinations_map_to_binding_and_credential_ids(tmp_path: Path):
    env_file = write_env(
        tmp_path,
        "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL=https://example.invalid/a\n"
        "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL=https://example.invalid/b\n"
        "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL=https://example.invalid/c\n",
    )
    packet = discord_contract.build_contract(build_matrix([env_file]))
    destinations = {item["target_name"]: item for item in packet["webhook_destinations"]}
    assert set(destinations) == {"announcements", "substack_drops", "product_updates"}
    assert destinations["announcements"]["destination_binding_id"] == "discord_announcements_capital_chronicle_01"
    assert destinations["substack_drops"]["destination_binding_id"] == "discord_substack_drops_capital_chronicle_01"
    assert destinations["product_updates"]["destination_binding_id"] == "discord_product_updates_capital_chronicle_01"
    assert destinations["announcements"]["credential_handle_id"] == "discord_announcements_webhook_01"
    assert destinations["substack_drops"]["credential_handle_id"] == "discord_substack_drops_webhook_01"
    assert destinations["product_updates"]["credential_handle_id"] == "discord_product_updates_webhook_01"
    assert all(item["live_write_allowed_now"] is False for item in destinations.values())


def test_public_and_operator_private_channel_groups_are_distinct(tmp_path: Path):
    env_file = write_env(
        tmp_path,
        "DISCORD_ANNOUNCEMENTS_CHANNEL_ID=public\n"
        "DISCORD_OPERATOR_QUEUE_CHANNEL_ID=private\n"
        "DISCORD_AUDIT_LOG_CHANNEL_ID=audit\n",
    )
    packet = discord_contract.build_contract(build_matrix([env_file]))
    public = packet["channel_groups"]["public_channels"]
    private = packet["channel_groups"]["operator_private_channels"]
    assert public["group_name"] == "public_channels"
    assert private["group_name"] == "operator_private_channels"
    assert private["destination_binding_id"] == "discord_operator_private_capital_chronicle_01"
    assert "DISCORD_ANNOUNCEMENTS_CHANNEL_ID" in public["key_status"]
    assert "DISCORD_OPERATOR_QUEUE_CHANNEL_ID" in private["key_status"]
    assert "DISCORD_OPERATOR_QUEUE_CHANNEL_ID" not in public["key_status"]


def test_role_keys_are_recognized_and_bot_deferred_not_required(tmp_path: Path):
    env_file = write_env(
        tmp_path,
        "DISCORD_ROLE_FOUNDER=raw-founder-secret-value\n"
        "DISCORD_ROLE_MODERATOR=moderator\n"
        "DISCORD_ROLE_CONTRIBUTOR=contributor\n"
        "DISCORD_ROLE_MEMBER=member\n"
        "DISCORD_ROLE_SUBSCRIBER=subscriber\n",
    )
    packet = discord_contract.build_contract(build_matrix([env_file]))
    roles = packet["role_groups"]["community_roles"]["key_status"]
    assert all(state["present"] is True for state in roles.values())
    assert packet["bot_deferred"] is True
    assert packet["bot_credential_handle_id"] == "discord_bot_capital_chronicle_01_deferred"


def test_missing_generic_discord_webhook_url_does_not_block_specific_webhooks(tmp_path: Path):
    env_file = write_env(tmp_path, "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL=https://example.invalid/b\n")
    matrix_packet = build_matrix([env_file])
    packet = discord_contract.build_contract(matrix_packet)
    assert packet["capability_class"] == "ready_webhook"
    destinations = {item["key_name"]: item for item in packet["webhook_destinations"]}
    assert destinations["DISCORD_SUBSTACK_DROPS_WEBHOOK_URL"]["capability_class"] == "ready_webhook"


def test_platform_registry_required_taxonomy_and_postures(tmp_path: Path):
    env_file = write_env(
        tmp_path,
        "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL=https://example.invalid/a\n"
        "THREADS_USER_ACCESS_TOKEN=threads\n"
        "META_ACCESS_TOKEN=meta\n"
        "NINE_ROUTER_API_KEY=provider\n",
    )
    packet = registry_contract.build_registry(build_matrix([env_file]))
    assert set(packet["platform_families"]) == {
        "owned_long_form",
        "community",
        "remote_operator",
        "social_distribution",
        "media_video_later",
        "ai_provider",
        "local_assets",
        "governance",
        "operator_local",
    }
    assert set(packet["adapter_types"]) == {
        "webhook_adapter",
        "official_api_adapter",
        "browser_cdp_adapter",
        "manual_fallback_adapter",
        "deferred_adapter",
    }
    assert row(packet, "discord")["current_execution_posture"] == "ready_webhook_but_live_disabled"
    assert row(packet, "threads")["current_execution_posture"] == "scope_proof_required"
    assert row(packet, "threads")["matrix_capability_class"] == "credential_present_scope_proof_required"
    assert row(packet, "nine_router")["current_execution_posture"] == "scope_proof_required"
    assert row(packet, "nine_router")["matrix_capability_class"] == "provider_present_live_gate_required"
    assert all(item["live_write_allowed_now"] is False for item in packet["platforms"])


def test_registry_keeps_manual_and_deferred_states():
    packet = registry_contract.build_registry(build_matrix([]))
    assert row(packet, "x_manual")["current_execution_posture"] == "manual_only"
    assert row(packet, "linkedin_personal_deferred")["current_execution_posture"] == "deferred_after_final_product"
    assert row(packet, "linkedin_org_deferred")["current_execution_posture"] == "deferred_after_final_product"
    assert row(packet, "tiktok_deferred")["current_execution_posture"] == "deferred_after_final_product"
    assert row(packet, "threads")["display_name"] == "Threads"
    assert row(packet, "facebook_page")["display_name"] == "Facebook Page"
