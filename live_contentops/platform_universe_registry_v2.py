"""Platform universe registry v2 (LOCAL, NOT LIVE).

Codifies Capital Chronicle primary channels after Telegram dispatch freeze.
No platform API, credential, scheduler, posting, scraping, or network behavior.
"""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = (
    "TASK_CONTENTOPS_0174WY_WZ_XA_PLATFORM_UNIVERSE_REGISTRY_V2_"
    "PRIMARY_CHANNELS_V0"
)
MODEL = "PLATFORM_UNIVERSE_REGISTRY_V2_0174WY_WZ_XA"
MODEL_VERSION = "0174WY_WZ_XA_PLATFORM_UNIVERSE_REGISTRY_V2_V1"
SOURCE_BASELINE_COMMIT = "d0e8d7f0e3c9bf84704cb66c602e75f7b9e8af62"
DOC_REL_DIR = os.path.join("docs", "automation", "0174WY_WZ_XA")

PRIMARY_BRAND_CHANNELS = ["x", "telegram", "substack"]
SECONDARY_CHANNELS = ["linkedin"]
EXPANSION_CHANNELS = ["threads", "instagram", "facebook_page"]
LATER_CHANNELS = ["tiktok", "youtube"]
PAYLOAD_CLASSES = [
    "x_short_post",
    "x_thread",
    "telegram_channel_update",
    "telegram_operator_review_message",
    "substack_newsletter_issue",
    "substack_longform_post",
    "linkedin_professional_post",
    "threads_short_post",
    "instagram_carousel_script",
    "facebook_page_post",
]
SUBSTACK_EXPORT_FIELDS = [
    "markdown_body",
    "newsletter_issue_structure",
    "title_subtitle_candidates",
    "hook",
    "thesis_or_question",
    "source_notes",
    "limitations",
    "no_signal_disclaimer",
    "seo_metadata",
    "cross_platform_derivatives",
    "export_status",
]

REGISTRY_PACKET = "platform_universe_registry_v2_packet.json"
REGISTRY_DOC = "platform_universe_registry_v2.md"
PRIMARY_PACKET = "primary_brand_channels_contract_packet.json"
PRIMARY_DOC = "primary_brand_channels_contract.md"
NEXT_PACKET = "next_product_direction_packet.json"
NEXT_DOC = "next_product_direction.md"


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def safety_flags():
    return {
        "is_local_only": True,
        "network_performed": False,
        "telegram_api_called": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "credential_read": False,
        "env_read": False,
        "dotenv_read": False,
        "scheduler_enabled": False,
        "live_post_performed": False,
        "autonomous_replies_or_dms": False,
        "scraping_performed": False,
        "substack_api_called": False,
        "x_api_called": False,
        "linkedin_api_called": False,
        "meta_api_called": False,
        "tiktok_or_youtube_api_called": False,
    }


def build_registry():
    registry = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "primary_brand_channels": PRIMARY_BRAND_CHANNELS,
        "secondary_channels": SECONDARY_CHANNELS,
        "expansion_channels": EXPANSION_CHANNELS,
        "later_channels": LATER_CHANNELS,
        "platform_roles": {
            "x": {
                "role": "narrative_velocity_short_form_distribution_public_discussion_threads_hooks_fast_feedback",
                "execution_status": "dry_run_first",
                "cost_rate_spend_gates": "later",
                "autonomous_replies_or_dms_allowed": False,
                "signal_framing_allowed": False,
            },
            "telegram": {
                "roles": ["remote_operator_inbox", "supervised_channel_dispatch_destination"],
                "roles_must_never_collapse": True,
                "dispatch_status": "proven_frozen",
                "inbox_status": "needs_product_buildout",
            },
            "substack": {
                "role": "primary_owned_audience_long_form_authority_channel",
                "owned_media": True,
                "initial_support": "manual_markdown_newsletter_export_first",
                "api_call_allowed_now": False,
                "credentials_allowed_now": False,
                "posting_allowed_now": False,
            },
            "linkedin": {
                "role": "professional_credibility_founder_product_positioning",
                "permission_review_gated": True,
                "main_growth_engine": False,
            },
            "threads": {"role": "lightweight_conversation_mirror_expansion_surface", "execution_status": "dry_run_only"},
            "instagram": {
                "role": "visual_education_carousel_layer",
                "requires": ["media_tray", "alt_text", "rights_status", "visual_workflow"],
                "execution_status": "dry_run_only",
            },
            "facebook_page": {"role": "meta_secondary_distribution_paired_with_instagram_later", "execution_status": "dry_run_only"},
            "tiktok": {"role": "video_workflow_later_only", "execution_status": "later_only"},
            "youtube": {"role": "video_workflow_later_only", "execution_status": "later_only"},
        },
        "payload_classes": PAYLOAD_CLASSES,
        "substack_manual_export_contract": {
            "owned_media_not_just_platform_adapter": True,
            "fields": SUBSTACK_EXPORT_FIELDS,
            "export_status_allowed_values": ["ready_for_manual_review", "blocked"],
            "no_substack_api_call": True,
            "no_credentials": True,
            "no_posting": True,
        },
        "next_product_direction": [
            "remote_operator_inbox",
            "intent_ingress_dry_run",
            "intent_parser",
            "editorial_workflow",
            "approval_authority",
            "dispatch_preparation",
            "evidence_cockpit_integration",
        ],
        "status": "pass",
    }
    registry["platform_universe_registry_checksum"] = adapter.compute_checksum(registry)
    return registry


def build_primary_brand_channels_contract(registry):
    contract = {
        "task_label": "TASK_CONTENTOPS_0174WY_WZ_XA_PRIMARY_BRAND_CHANNELS_CONTRACT_V0",
        "model": "PRIMARY_BRAND_CHANNELS_CONTRACT_0174WY_WZ_XA",
        "model_version": "0174WY_WZ_XA_PRIMARY_BRAND_CHANNELS_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "primary_brand_channels": registry["primary_brand_channels"],
        "primary_channel_roles": {k: registry["platform_roles"][k] for k in registry["primary_brand_channels"]},
        "payload_classes": registry["payload_classes"],
        "platform_universe_registry_checksum": registry["platform_universe_registry_checksum"],
    }
    contract["primary_brand_channels_contract_checksum"] = adapter.compute_checksum(contract)
    return contract


def build_next_product_direction(registry):
    direction = {
        "task_label": "TASK_CONTENTOPS_0174WY_WZ_XA_NEXT_PRODUCT_DIRECTION_V0",
        "model": "NEXT_PRODUCT_DIRECTION_0174WY_WZ_XA",
        "model_version": "0174WY_WZ_XA_NEXT_PRODUCT_DIRECTION_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "direction": "remote_operator_inbox_and_intent_ingress_dry_run",
        "telegram_dispatch_status": "proven_frozen",
        "no_more_ledger_treadmill": True,
        "product_work": registry["next_product_direction"],
        "exact_next_batch_prompt": (
            "TASK_CONTENTOPS_0174XB_XC_XD_REMOTE_OPERATOR_INBOX_INTENT_INGRESS_"
            "DRY_RUN_BATCH_V0"
        ),
        "platform_universe_registry_checksum": registry["platform_universe_registry_checksum"],
    }
    direction["next_product_direction_checksum"] = adapter.compute_checksum(direction)
    return direction


def render_doc(title, packet):
    lines = [f"# {title}", ""]
    for key in sorted(packet):
        value = packet[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root=".", output_dir=None):
    output_dir = output_dir or (pathlib.Path(repo_root) / DOC_REL_DIR)
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    primary = build_primary_brand_channels_contract(registry)
    direction = build_next_product_direction(registry)
    packets = [
        (REGISTRY_PACKET, registry),
        (PRIMARY_PACKET, primary),
        (NEXT_PACKET, direction),
    ]
    docs = [
        (REGISTRY_DOC, "Platform Universe Registry V2", registry),
        (PRIMARY_DOC, "Primary Brand Channels Contract", primary),
        (NEXT_DOC, "Next Product Direction", direction),
    ]
    for name, packet in packets:
        (out / name).write_text(adapter.serialize(packet), encoding="utf-8", newline="\n")
    for name, title, packet in docs:
        (out / name).write_text(render_doc(title, packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"registry": registry, "primary_contract": primary, "next_direction": direction})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("PRIMARY_BRAND_CHANNELS", ",".join(result["registry"]["primary_brand_channels"]))
    print("PLATFORM_UNIVERSE_REGISTRY_CHECKSUM", result["registry"]["platform_universe_registry_checksum"])
    print("PRIMARY_BRAND_CHANNELS_CONTRACT_CHECKSUM", result["primary_contract"]["primary_brand_channels_contract_checksum"])
    print("NEXT_PRODUCT_DIRECTION_CHECKSUM", result["next_direction"]["next_product_direction_checksum"])
