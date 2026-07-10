import os
import re
from pathlib import Path

def test_no_forbidden_imports_or_env_vars():
    root = Path(__file__).parent.parent / "live_contentops"

    # Policy B & C: Forbidden network, provider, and platform imports
    forbidden_imports = re.compile(
        r"import\s+(requests|httpx|socket|openai|anthropic|tweepy|selenium|playwright|dotenv)"
    )
    urllib_network_imports = re.compile(
        r"(?:from\s+urllib\.(request|error)\s+import|import\s+urllib\.(request|error))"
    )

    # Policy A: Env-like access
    env_access = re.compile(r"os\.(environ|getenv)")

    # Explicitly authorized live-gate modules
    live_gate_allowlist = {
        "telegram_live_pilot.py",
        "telegram_live_getme_gate.py",
        "telegram_target_binding_gate.py",
        "telegram_first_supervised_live_post_gate.py",
        "telegram_second_supervised_live_post_gate.py",
        "telegram_read_only_identity_pilot.py",
        "telegram_live_sendmessage_pilot.py",
        "facebook_page_adapter_v6.py",
        "instagram_adapter_v6.py",
        "threads_adapter_v6.py",
        "discord_live_adapter_v6.py",
        "eight_platform_substack_first_pipeline_v1.py",
        "telegram_live_adapter_v6.py",
        "substack_browser_adapter_v6.py",
        "x_browser_adapter_v6.py",
        "linkedin_browser_adapter_v6.py",
        "live_telemetry_v6.py",
        "scheduler_v6.py",
        "google_image_search_v6.py",
        "platform_native_variant_generator_live_v6.py",
        "live_production_pipeline_runner_v6.py",
        "fast_one_cycle_automation_v0.py",
        "grounded_search_engine_v6.py",
    }
    urllib_network_allowlist = live_gate_allowlist | {
        "current_oil_release_source_v1.py",
        "edge_cdp_publishing_adapter_v1.py",
        "live_readonly_probe_registry.py",
        "media_content_audit_v6.py",
        "media_manifest_authority_v1.py",
        "publishing_profile_registry_v1.py",
    }

    # Modules allowed to perform env lookups for configuration (excluding generic modules)
    env_access_allowlist = {
        "cli.py",
        "operator_browser_lab.py",
        "social_credential_setup_workbench.py",
        "ai_provider_gate_v6.py",
        "operator_recovery_to_explicit_live_scope_gate_source_candidate_v6.py",
        "discord_supervised_live_preflight_v6.py",
        "grounded_news_angle_workbench.py",
        "publishing_profile_registry_v1.py",
        "source_chart_short_video_v1.py",
        "video_platform_capability_matrix_v1.py",
    }

    for p in root.rglob("*.py"):
        text = p.read_text(encoding="utf-8")

        # 1. Network/platform/provider imports check (strict denylist)
        if forbidden_imports.search(text):
            assert p.name in live_gate_allowlist, (
                f"Forbidden network/provider/platform import found in {p.name}. "
                "Only explicitly authorized live-gate modules may import these libraries."
            )
        if urllib_network_imports.search(text):
            assert p.name in urllib_network_allowlist, (
                f"Forbidden urllib network import found in {p.name}. "
                "Only explicitly authorized live-gate or read-only fetch modules may import urllib.request/urllib.error."
            )

        # 2. Env access check
        if env_access.search(text):
            is_authorized_live = p.name in live_gate_allowlist
            is_config_cli = p.name in env_access_allowlist
            is_readiness_module = "presence_check" in p.name or "readiness" in p.name

            assert is_authorized_live or is_config_cli or is_readiness_module, (
                f"Unauthorized env-like access (os.environ/os.getenv) found in {p.name}. "
                "Only authorized live-gate, CLI config, or local readiness/presence check modules are permitted."
            )
