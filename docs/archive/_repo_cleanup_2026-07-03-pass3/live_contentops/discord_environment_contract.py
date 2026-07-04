"""Discord environment and binding contract derived from redacted matrix only."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from live_contentops.unified_credential_capability_matrix import build_matrix

TASK_LABEL = "TASK_CONTENTOPS_V6_PLATFORM_REGISTRY_AND_DISCORD_ENVIRONMENT_CONTRACT_V0"
SCHEMA_VERSION = "discord_environment_contract.v1"

GUILD_IDENTITY_KEYS = ("DISCORD_SERVER_ID", "DISCORD_GUILD_ID")
PUBLIC_CHANNEL_KEYS = (
    "DISCORD_ANNOUNCEMENTS_CHANNEL_ID",
    "DISCORD_SUBSTACK_DROPS_CHANNEL_ID",
    "DISCORD_PRODUCT_UPDATES_CHANNEL_ID",
    "DISCORD_RESEARCH_QUESTIONS_CHANNEL_ID",
    "DISCORD_CONTENT_IDEAS_CHANNEL_ID",
    "DISCORD_ASK_JIM_CHANNEL_ID",
    "DISCORD_FEEDBACK_CHANNEL_ID",
)
OPERATOR_PRIVATE_CHANNEL_KEYS = (
    "DISCORD_OPERATOR_QUEUE_CHANNEL_ID",
    "DISCORD_APPROVAL_CHECKPOINTS_CHANNEL_ID",
    "DISCORD_BROWSER_CHECKPOINTS_CHANNEL_ID",
    "DISCORD_AUDIT_LOG_CHANNEL_ID",
    "DISCORD_MANUAL_FALLBACK_CHANNEL_ID",
)
ROLE_KEYS = (
    "DISCORD_ROLE_FOUNDER",
    "DISCORD_ROLE_MODERATOR",
    "DISCORD_ROLE_CONTRIBUTOR",
    "DISCORD_ROLE_MEMBER",
    "DISCORD_ROLE_SUBSCRIBER",
)
WEBHOOK_KEYS = (
    "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL",
    "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL",
    "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL",
)


@dataclass(frozen=True)
class WebhookDestination:
    target_name: str
    key_name: str
    destination_binding_id: str
    credential_handle_id: str


WEBHOOK_DESTINATIONS: tuple[WebhookDestination, ...] = (
    WebhookDestination("announcements", "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL", "discord_announcements_capital_chronicle_01", "discord_announcements_webhook_01"),
    WebhookDestination("substack_drops", "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL", "discord_substack_drops_capital_chronicle_01", "discord_substack_drops_webhook_01"),
    WebhookDestination("product_updates", "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL", "discord_product_updates_capital_chronicle_01", "discord_product_updates_webhook_01"),
)

OPERATOR_BINDING_ID = "discord_operator_private_capital_chronicle_01"
BOT_CREDENTIAL_HANDLE_ID = "discord_bot_capital_chronicle_01_deferred"


def _row(packet: dict, platform: str) -> dict:
    for item in packet.get("platform_rows", []):
        if item.get("platform") == platform:
            return item
    return {"key_status": {}, "key_value_status": {}, "capability_class": "missing_matrix_row", "live_write_eligible": False, "live_write_allowed_now": False}


def _status(keys: tuple[str, ...], matrix_rows: tuple[dict, ...]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for key in keys:
        present = False
        value_status = "missing"
        for row in matrix_rows:
            if key in row.get("key_status", {}):
                present = bool(row["key_status"].get(key))
                value_status = row.get("key_value_status", {}).get(key, "missing")
                break
        result[key] = {"present": present, "value_status": value_status}
    return result


def build_contract(capability_packet: dict | None = None) -> dict:
    packet = capability_packet or build_matrix([".env", ".env.local"])
    webhook_row = _row(packet, "Discord webhooks")
    binding_row = _row(packet, "Discord guild/server/channel/role IDs")
    bot_row = _row(packet, "Discord bot deferred")
    matrix_rows = (webhook_row, binding_row, bot_row)

    webhook_destinations = []
    for destination in WEBHOOK_DESTINATIONS:
        key_state = _status((destination.key_name,), (webhook_row,))[destination.key_name]
        webhook_destinations.append({
            **asdict(destination),
            "key_status": key_state,
            "capability_class": "ready_webhook" if key_state["present"] and key_state["value_status"] == "nonblank" else "credential_missing",
            "live_write_eligible": bool(key_state["present"] and key_state["value_status"] == "nonblank"),
            "live_write_allowed_now": False,
        })

    return {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "source_matrix_schema_version": packet.get("schema_version"),
        "capability_class": webhook_row.get("capability_class"),
        "live_write_eligible": bool(webhook_row.get("live_write_eligible")),
        "live_write_allowed_now": False,
        "bot_deferred": True,
        "bot_credential_handle_id": BOT_CREDENTIAL_HANDLE_ID,
        "bot_capability_class": bot_row.get("capability_class"),
        "guild_server_identity": {
            "group_name": "guild_server_identity",
            "key_status": _status(GUILD_IDENTITY_KEYS, matrix_rows),
        },
        "channel_groups": {
            "public_channels": {
                "group_name": "public_channels",
                "key_status": _status(PUBLIC_CHANNEL_KEYS, matrix_rows),
            },
            "operator_private_channels": {
                "group_name": "operator_private_channels",
                "destination_binding_id": OPERATOR_BINDING_ID,
                "key_status": _status(OPERATOR_PRIVATE_CHANNEL_KEYS, matrix_rows),
            },
        },
        "role_groups": {
            "community_roles": {
                "group_name": "community_roles",
                "key_status": _status(ROLE_KEYS, matrix_rows),
            }
        },
        "webhook_destinations": webhook_destinations,
        "redaction_policy": {
            "raw_webhook_url_output": False,
            "token_output": False,
            "token_length_prefix_suffix_hash_output": False,
            "cookie_session_local_storage_output": False,
            "browser_profile_storage_output": False,
            "raw_env_line_output": False,
        },
    }


def write_packet(packet: dict, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build redacted Discord environment packet")
    parser.add_argument("--matrix-packet", default="docs/automation/V6_CREDENTIAL_CAPABILITY_MATRIX/redacted_capability_matrix_packet.json", help="Redacted capability matrix packet path")
    parser.add_argument("--output", default=None, help="Optional output path")
    args = parser.parse_args(argv)
    capability_packet = json.loads(Path(args.matrix_packet).read_text(encoding="utf-8"))
    packet = build_contract(capability_packet)
    if args.output:
        write_packet(packet, args.output)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
