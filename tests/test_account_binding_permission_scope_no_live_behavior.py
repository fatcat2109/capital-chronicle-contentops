from pathlib import Path

TASK_FILES = [
    Path("live_contentops/account_binding_permission_scope_verifier.py"),
    Path("live_contentops/platform_scope_permission_contract.py"),
]

FORBIDDEN_SNIPPETS = (
    "os.environ",
    "getenv(",
    "dotenv",
    "import requests",
    "from requests",
    "import urllib",
    "from urllib",
    "import http.client",
    "from http.client",
    "import socket",
    "from socket",
    "import aiohttp",
    "from aiohttp",
    "import telegram",
    "from telegram",
    "import tweepy",
    "from tweepy",
    "import linkedin",
    "from linkedin",
    "import facebook_business",
    "from facebook_business",
    "import googleapiclient",
    "from googleapiclient",
    "playwright",
    "selenium",
    "chrome",
    "cdp",
    "subprocess",
    "sendMessage",
    "statuses/update",
    "ugcPosts",
    "/me/feed",
    "media_publish",
    "video/upload",
    "videos.insert",
)


def _read_task_sources():
    root = Path(__file__).resolve().parents[1]
    return {path.as_posix(): (root / path).read_text(encoding="utf-8") for path in TASK_FILES}


def test_new_modules_do_not_import_live_or_browser_capabilities():
    sources = _read_task_sources()
    for filename, source in sources.items():
        lowered = source.lower()
        for forbidden in FORBIDDEN_SNIPPETS:
            assert forbidden.lower() not in lowered, (filename, forbidden)


def test_new_modules_expose_no_live_write_ready_now_claims():
    sources = _read_task_sources()
    for filename, source in sources.items():
        assert "live_write_allowed_now: bool = False" in source or "live_write_allowed_now=False" in source, filename
        assert "credential_hydration_allowed_in_this_task" in source, filename
        assert "read_only_probe_allowed_in_this_task" in source, filename


def test_no_ui_or_browser_qa_files_are_part_of_task_contract():
    task_file_names = {path.as_posix() for path in TASK_FILES}
    assert all(not name.startswith("ui/") for name in task_file_names)
    assert all("playwright" not in name.lower() for name in task_file_names)
    assert all("screenshot" not in name.lower() for name in task_file_names)


def test_packet_builders_do_not_require_repo_root_env_or_credentials():
    from live_contentops.account_binding_permission_scope_verifier import account_binding_permission_scope_packet
    from live_contentops.platform_scope_permission_contract import platform_scope_permission_contract_packet

    binding_packet = account_binding_permission_scope_packet()
    contract_packet = platform_scope_permission_contract_packet()
    assert binding_packet["credential_hydration_performed"] is False
    assert binding_packet["credential_hydration_allowed_in_this_task"] is False
    assert binding_packet["read_only_probe_performed"] is False
    assert binding_packet["read_only_probe_allowed_in_this_task"] is False
    assert contract_packet["credential_hydration_allowed_in_this_task"] is False
    assert contract_packet["read_only_probe_allowed_in_this_task"] is False
