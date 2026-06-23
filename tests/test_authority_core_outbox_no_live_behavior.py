from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "live_contentops" / "dispatch_outbox.py",
    ROOT / "live_contentops" / "idempotency_policy.py",
    ROOT / "live_contentops" / "kill_switch_policy.py",
    ROOT / "live_contentops" / "redacted_dispatch_audit.py",
]
COMBINED = "\n".join(path.read_text(encoding="utf-8") for path in FILES)


def test_no_env_reads():
    forbidden = ["os.environ", "getenv(", "dotenv", ".env"]
    assert not any(term in COMBINED for term in forbidden)


def test_no_network_imports():
    forbidden = ["import requests", "import httpx", "import aiohttp", "import urllib", "import socket", "import ssl"]
    assert not any(term in COMBINED for term in forbidden)


def test_no_platform_sdk_imports():
    forbidden = ["import tweepy", "import telegram", "import facebook", "import linkedin", "import openai", "import anthropic"]
    assert not any(term in COMBINED for term in forbidden)


def test_no_browser_cdp_imports():
    forbidden = ["playwright", "selenium", "chrome", "cdp", "browser"]
    assert not any(term in COMBINED.lower() for term in forbidden)


def test_no_subprocess_imports():
    assert "subprocess" not in COMBINED


def test_no_live_send_post_upload_calls():
    forbidden = [".send(", ".post(", ".upload(", "live_send", "platform_api_called = True", "live_request_performed = True"]
    assert not any(term in COMBINED for term in forbidden)


def test_no_ui_files_changed_by_task_contract():
    task_files = [str(path.relative_to(ROOT)).replace("\\", "/") for path in FILES]
    assert all(not path.startswith(("ui/", "web/", "frontend/", "app/")) for path in task_files)
