from pathlib import Path

TASK_FILES = [
    Path("live_contentops/live_gate_state_machine.py"),
    Path("live_contentops/platform_error_classifier.py"),
    Path("live_contentops/live_gate_endpoint_contract.py"),
]

FORBIDDEN_SUBSTRINGS = [
    "os.environ",
    "getenv(",
    "import requests",
    "from requests",
    "urllib.request",
    "http.client",
    "import webbrowser",
    "import selenium",
    "import playwright",
    "import subprocess",
    "import socket",
    "sendMessage(",
    ".post(",
    "upload(",
    "execute_cdp_cmd",
    "localStorage",
    "sessionStorage",
]


def test_task_modules_have_no_network_env_browser_or_subprocess_behavior():
    root = Path(__file__).resolve().parents[1]
    for relative in TASK_FILES:
        text = (root / relative).read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SUBSTRINGS:
            assert forbidden not in text, f"{relative} contains forbidden substring {forbidden}"


def test_task_modules_do_not_import_platform_sdks():
    root = Path(__file__).resolve().parents[1]
    forbidden_imports = ["import tweepy", "googleapiclient", "facebook_business", "from linkedin", "TikTokApi", "instagrapi"]
    for relative in TASK_FILES:
        text = (root / relative).read_text(encoding="utf-8")
        for forbidden in forbidden_imports:
            assert forbidden not in text


def test_task_owned_paths_are_core_and_tests_only():
    task_paths = [str(path).replace("\\", "/") for path in TASK_FILES]
    task_paths.extend([
        "tests/test_live_gate_state_machine.py",
        "tests/test_platform_error_classifier.py",
        "tests/test_live_gate_endpoint_contract.py",
        "tests/test_live_gate_no_live_behavior.py",
    ])
    assert not any(path.startswith("ui/") or "/browser_qa/" in path or "/design/" in path for path in task_paths)


def test_no_live_behavior_packet_contract_values():
    from live_contentops.live_gate_endpoint_contract import live_gate_endpoint_contract_packet
    from live_contentops.live_gate_state_machine import live_gate_state_machine_packet
    from live_contentops.platform_error_classifier import platform_error_classifier_packet

    gate_packet = live_gate_state_machine_packet()
    endpoint_packet = live_gate_endpoint_contract_packet()
    classifier_packet = platform_error_classifier_packet()
    assert gate_packet["all_valid_for_live_dispatch_now_false"] is True
    assert gate_packet["auto_retry_allowed_any"] is False
    assert endpoint_packet["live_write_allowed_in_this_task_any"] is False
    assert endpoint_packet["read_only_probe_allowed_in_this_task_any"] is False
    assert classifier_packet["unknown_error_auto_retry_allowed"] is False
    assert classifier_packet["rate_limit_auto_retry_allowed"] is False
