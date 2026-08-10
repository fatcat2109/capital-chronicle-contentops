from live_contentops import publishing_profile_registry_v1 as registry


def _process(name: str, pid: int, command_line: str) -> dict:
    return {"Name": name, "ProcessId": pid, "CommandLine": command_line}


def test_registry_declares_edge_only_canonical_authority():
    packet = registry.canonical_profile_registry()
    assert packet["browser_family"] == "microsoft_edge"
    assert packet["chrome_publishing_allowed"] is False
    assert packet["allowed_cdp_ports"] == [9223]
    assert packet["ingestion_only_cdp_port"] == 9222


def test_doctor_ignores_ingestion_chrome_and_locks_publishing_to_9223(monkeypatch):
    chrome = _process(
        "chrome.exe",
        101,
        r'chrome.exe --remote-debugging-port=9222 --user-data-dir="A:\Capital Chronicle\tools\chrome-contentops-x-cdp"',
    )
    monkeypatch.setattr(registry, "probe_cdp_version", lambda port: {"cdp_alive": port == 9222, "browser_family": "non_edge_browser" if port == 9222 else None, "websocket_available": port == 9222})
    report = registry.browser_doctor(processes=[chrome])
    by_port = {row["cdp_port"]: row for row in report["ports"]}
    assert 9222 not in by_port
    assert list(by_port) == [9223]
    assert report["recommended_cdp_port"] == 9223
    assert report["status"] == "READY_TO_LAUNCH"


def test_doctor_accepts_only_edge_with_exact_contentops_profile(monkeypatch):
    edge = _process(
        "msedge.exe",
        202,
        r'msedge.exe --remote-debugging-port=9223 --user-data-dir="A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"',
    )
    monkeypatch.setattr(registry, "probe_cdp_version", lambda _port: {"cdp_alive": True, "browser_family": "microsoft_edge", "websocket_available": True})
    report = registry.browser_doctor(processes=[edge])
    assert report["status"] == "READY_TO_ATTACH"
    assert report["recommended_cdp_port"] == 9223


def test_edge_command_rejects_non_edge_binary():
    try:
        registry.build_edge_command("chrome.exe", cdp_port=9222, urls=["https://substack.com/"])
    except registry.PublishingProfileError as error:
        assert str(error) == "publishing_browser_must_be_microsoft_edge"
    else:
        raise AssertionError("Chrome must not build a publishing command")
