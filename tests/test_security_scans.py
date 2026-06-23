import os
import re
from pathlib import Path

def test_no_forbidden_imports_or_env_vars():
    root = Path(__file__).parent.parent / "live_contentops"

    # Policy B & C: Forbidden network, provider, and platform imports
    forbidden_imports = re.compile(
        r"import\s+(requests|httpx|urllib|socket|openai|anthropic|tweepy|selenium|playwright|dotenv)"
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
    }

    # Modules allowed to perform env lookups for configuration (excluding generic modules)
    env_access_allowlist = {
        "cli.py",
        "operator_browser_lab.py",
        "social_credential_setup_workbench.py",
    }

    for p in root.rglob("*.py"):
        text = p.read_text(encoding="utf-8")

        # 1. Network/platform/provider imports check (strict denylist)
        if forbidden_imports.search(text):
            assert p.name in live_gate_allowlist, (
                f"Forbidden network/provider/platform import found in {p.name}. "
                "Only explicitly authorized live-gate modules may import these libraries."
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
