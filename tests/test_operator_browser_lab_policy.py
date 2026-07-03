from pathlib import Path
from live_contentops import operator_browser_lab as lab


def test_default_profile_path_outside_repo():
    repo = Path(r"A:\Capital Chronicle\tools\cc-live-contentops")
    profile = lab.get_default_profile_root()
    assert not lab.is_path_inside(profile, repo)
    policy = lab.validate_profile_policy(profile, repo)
    assert policy["profile_inside_repo"] is False
    assert policy["profile_path_persistable_in_git"] is False


def test_cdp_default_port_and_override():
    assert lab.resolve_cdp_port({}) == 9222
    assert lab.resolve_cdp_port({lab.CDP_PORT_ENV_KEY: "9333"}) == 9333


def test_browser_command_never_includes_secrets():
    cmd = lab.build_browser_command("chrome.exe", Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"), 9222, "telegram")
    joined = "\n".join(cmd).lower()
    assert "bot_token" not in joined
    assert "client_secret" not in joined
    assert "access_token" not in joined
    assert "cookie" not in joined
    assert "--new-window" in cmd
    assert "https://core.telegram.org/bots/api" in cmd


def test_policy_forbids_browser_state_dumps_and_publish_actions():
    policy = lab.SAFE_POLICY
    assert policy["cookie_dump_allowed"] is False
    assert policy["localStorage_dump_allowed"] is False
    assert policy["sessionStorage_dump_allowed"] is False
    assert policy["dom_dump_allowed"] is False
    assert policy["platform_write_allowed"] is False
    assert policy["post_publish_upload_allowed"] is False
    assert policy["scheduler_allowed"] is False
    assert policy["autonomous_replies_or_dms_allowed"] is False


def test_all_docs_contains_official_portals():
    urls = lab.urls_for_platform("all-docs")
    assert "https://developer.x.com/" in urls
    assert "https://www.linkedin.com/developers/" in urls
    assert "https://developers.facebook.com/" in urls
    assert "https://developers.tiktok.com/" in urls
    assert "https://console.cloud.google.com/" in urls
    assert "https://substack.com/" in urls
