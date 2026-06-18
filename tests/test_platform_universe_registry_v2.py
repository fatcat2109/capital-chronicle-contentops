import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_PAYLOAD_CLASSES = [
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


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.platform_universe_registry_v2")
    assert callable(module.write_artifacts)
    assert module.TASK_LABEL.startswith("TASK_CONTENTOPS_0174WY_WZ_XA")


def test_primary_secondary_expansion_later_channels():
    module = importlib.import_module("live_contentops.platform_universe_registry_v2")
    registry = module.build_registry()
    assert registry["primary_brand_channels"] == ["x", "telegram", "substack"]
    assert registry["secondary_channels"] == ["linkedin"]
    assert registry["expansion_channels"] == ["threads", "instagram", "facebook_page"]
    assert registry["later_channels"] == ["tiktok", "youtube"]


def test_substack_primary_owned_media_manual_export_first():
    module = importlib.import_module("live_contentops.platform_universe_registry_v2")
    substack = module.build_registry()["platform_roles"]["substack"]
    contract = module.build_registry()["substack_manual_export_contract"]
    assert substack["owned_media"] is True
    assert substack["initial_support"] == "manual_markdown_newsletter_export_first"
    assert substack["api_call_allowed_now"] is False
    assert contract["owned_media_not_just_platform_adapter"] is True
    assert contract["export_status_allowed_values"] == ["ready_for_manual_review", "blocked"]
    for field in module.SUBSTACK_EXPORT_FIELDS:
        assert field in contract["fields"]


def test_platform_roles_match_strategy():
    module = importlib.import_module("live_contentops.platform_universe_registry_v2")
    roles = module.build_registry()["platform_roles"]
    assert roles["x"]["execution_status"] == "dry_run_first"
    assert roles["x"]["autonomous_replies_or_dms_allowed"] is False
    assert roles["x"]["signal_framing_allowed"] is False
    assert roles["telegram"]["roles"] == ["remote_operator_inbox", "supervised_channel_dispatch_destination"]
    assert roles["telegram"]["roles_must_never_collapse"] is True
    assert roles["telegram"]["dispatch_status"] == "proven_frozen"
    assert roles["telegram"]["inbox_status"] == "needs_product_buildout"
    assert roles["linkedin"]["permission_review_gated"] is True
    assert roles["linkedin"]["main_growth_engine"] is False
    assert roles["threads"]["execution_status"] == "dry_run_only"
    assert roles["instagram"]["execution_status"] == "dry_run_only"
    assert roles["facebook_page"]["execution_status"] == "dry_run_only"
    assert roles["tiktok"]["execution_status"] == "later_only"
    assert roles["youtube"]["execution_status"] == "later_only"


def test_payload_classes_exactly_match_contract():
    module = importlib.import_module("live_contentops.platform_universe_registry_v2")
    assert module.build_registry()["payload_classes"] == EXPECTED_PAYLOAD_CLASSES


def test_no_live_api_credential_scheduler_posting_network_behavior():
    module = importlib.import_module("live_contentops.platform_universe_registry_v2")
    registry = module.build_registry()
    for key in [
        "network_performed", "telegram_api_called", "platform_api_called",
        "provider_api_called", "credential_read", "env_read", "dotenv_read",
        "scheduler_enabled", "live_post_performed", "autonomous_replies_or_dms",
        "scraping_performed", "substack_api_called", "x_api_called",
        "linkedin_api_called", "meta_api_called", "tiktok_or_youtube_api_called",
    ]:
        assert registry[key] is False


def test_primary_contract_and_next_direction():
    module = importlib.import_module("live_contentops.platform_universe_registry_v2")
    registry = module.build_registry()
    primary = module.build_primary_brand_channels_contract(registry)
    direction = module.build_next_product_direction(registry)
    assert primary["primary_brand_channels"] == ["x", "telegram", "substack"]
    assert direction["direction"] == "remote_operator_inbox_and_intent_ingress_dry_run"
    assert direction["telegram_dispatch_status"] == "proven_frozen"
    assert direction["no_more_ledger_treadmill"] is True
    assert direction["exact_next_batch_prompt"] == "TASK_CONTENTOPS_0174XB_XC_XD_REMOTE_OPERATOR_INBOX_INTENT_INGRESS_DRY_RUN_BATCH_V0"


def test_deterministic_packet_generation_and_unsafe_path_refusal(tmp_path):
    module = importlib.import_module("live_contentops.platform_universe_registry_v2")
    first = module.write_artifacts(REPO_ROOT)
    second = module.write_artifacts(REPO_ROOT)
    assert first == second
    assert (REPO_ROOT / module.DOC_REL_DIR / module.REGISTRY_PACKET).exists()
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        module.write_artifacts(REPO_ROOT, tmp_path)
