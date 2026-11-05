"""CC-297: every ContentOps key read goes through the one reader.

The real stores are replaced by in-memory fakes holding dummy values; each test removes the names
from the process environment first, as after Jim's move.
"""
from __future__ import annotations

import os
import re

import pytest

from live_contentops import secret_store_v1 as reader

STORE = {
    "THREADS_USER_ACCESS_TOKEN": "cc297-dummy-threads-token-0001",
    "THREADS_USER_ID": "cc297-dummy-threads-user",
    "TELEGRAM_BOT_TOKEN": "cc297-dummy-telegram-token-0001",
    "TELEGRAM_CHANNEL_ID": "-100cc297",
    "FACEBOOK_PAGE_ACCESS_TOKEN": "cc297-dummy-facebook-token-0001",
    "INSTAGRAM_ACCESS_TOKEN": "cc297-dummy-instagram-token-0001",
    "CLOUDINARY_CLOUD_NAME": "cc297dummycloud",
    "CLOUDINARY_API_KEY": "cc297-dummy-cloudinary-key",
    "CLOUDINARY_API_SECRET": "cc297-dummy-cloudinary-secret",
    "NINE_ROUTER_API_KEY": "cc297-dummy-nine-router-key",
    "LINKEDIN_CLIENT_ID": "cc297-dummy-linkedin-id",
    "LINKEDIN_CLIENT_SECRET": "cc297-dummy-linkedin-secret",
    "AI_API_CHEAP_API_KEY": "cc297-dummy-image-key-0001",
    "YOUTUBE_CLIENT_ID": "cc297-dummy-youtube-id",
    "YOUTUBE_CLIENT_SECRET": "cc297-dummy-youtube-secret",
    "YOUTUBE_REFRESH_TOKEN": "cc297-dummy-youtube-refresh",
    "YOUTUBE_CHANNEL_ID": "cc297-dummy-channel",
}
USER_ENV = {"DISCORD_ANNOUNCEMENTS_WEBHOOK_URL": "https://discord.invalid/api/webhooks/cc297/rotated-dummy"}
ALL_NAMES = set(STORE) | set(USER_ENV) | {
    "THREADS_ACCESS_TOKEN", "META_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID", "INSTAGRAM_IG_ID",
    "FACEBOOK_PAGE_ID", "TELEGRAM_TARGET_CHAT_ID", "TEST_TELEGRAM_CHANNEL", "TELEGRAM_CHAT_ID",
    "TEST_TELEGRAM_BOT_TOKEN", "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK", "DISCORD_WEBHOOK_URL",
    "LINKEDIN_OAUTH_REDIRECT_URI", "NINE_ROUTER_BASE_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
}


_KEY_LIKE = re.compile(r"(TOKEN|SECRET|KEY|WEBHOOK|PASSWORD|CLIENT|_ID$|CHANNEL|CLOUDINARY|TELEGRAM|THREADS|"
                       r"META_|FACEBOOK|INSTAGRAM|LINKEDIN|YOUTUBE|TIKTOK|NINE_ROUTER|DISCORD)", re.IGNORECASE)


def same(left, right) -> bool:
    """Compare without letting a failing assert print either value."""
    return left == right


@pytest.fixture
def moved(monkeypatch):
    """Keys in (fake) Credential Manager and live user environment; none in the process environment.

    The test process inherits Jim's real environment, so every key-like name is removed from it here
    (restored after the test; nothing is read out or printed).
    """
    for name in [key for key in list(os.environ) if _KEY_LIKE.search(key)] + sorted(ALL_NAMES):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(reader.STORE_MODE_ENV, reader.CREDENTIAL_MANAGER_MODE)

    def store_read(target):
        name = target[len(reader.TARGET_PREFIX):]
        return (reader.STORE_FOUND, STORE[name]) if name in STORE else (reader.STORE_NOT_FOUND, None)

    def store_list(prefix):
        return reader.STORE_FOUND, tuple((prefix + name, value) for name, value in STORE.items())

    monkeypatch.setattr(reader, "windows_store_read", store_read)
    monkeypatch.setattr(reader, "windows_user_env_read", lambda name: USER_ENV.get(name))
    monkeypatch.setattr(reader, "windows_store_list", store_list)
    return STORE


def test_threads_adapter_reads_credential_manager(moved):
    from live_contentops import threads_adapter_v6

    assert same(threads_adapter_v6._threads_token(), STORE["THREADS_USER_ACCESS_TOKEN"])
    assert same(threads_adapter_v6._threads_user_id(), STORE["THREADS_USER_ID"])
    assert same(threads_adapter_v6._threads_token("explicit"), "explicit")


def test_threads_probe_is_ready_from_credential_manager_alone(moved, monkeypatch, capfd):
    from live_contentops import destination_transport_registry_v1 as registry

    seen = {}

    def fake_json_get(url, *, timeout_seconds=8.0):
        seen["token_in_url"] = STORE["THREADS_USER_ACCESS_TOKEN"] in url
        seen["host"] = url.split("/")[2]
        return {"id": "cc297", "username": "official.capitalchronicle"}

    monkeypatch.setattr(registry, "_json_get", fake_json_get)
    row = registry.DestinationReadinessManager().probe_surface("THREADS_POST")
    state = str(row.get("readiness_state"))
    assert state == registry.READY_NON_BROWSER_BINDING, state
    assert row.get("write_eligible") is True
    assert state in registry.READY_STATES
    assert seen.get("token_in_url") is True and seen.get("host") == "graph.threads.net", sorted(seen)
    out, err = capfd.readouterr()
    assert STORE["THREADS_USER_ACCESS_TOKEN"] not in out + err + repr(row)


def test_telegram_meta_and_discord_adapters_read_the_reader(moved):
    from live_contentops import discord_live_adapter_v6, facebook_page_adapter_v6, instagram_adapter_v6
    from live_contentops import telegram_live_adapter_v6

    assert same(telegram_live_adapter_v6._get_default_bot_token(), STORE["TELEGRAM_BOT_TOKEN"])
    assert same(telegram_live_adapter_v6._get_default_chat_id(), STORE["TELEGRAM_CHANNEL_ID"])
    assert same(facebook_page_adapter_v6._facebook_token(), STORE["FACEBOOK_PAGE_ACCESS_TOKEN"])
    assert same(instagram_adapter_v6._instagram_token(), STORE["INSTAGRAM_ACCESS_TOKEN"])
    # The live user environment (rotated value) is read, not the stale process value.
    assert same(discord_live_adapter_v6._get_default_webhook_url(), USER_ENV["DISCORD_ANNOUNCEMENTS_WEBHOOK_URL"])


def test_readiness_manager_passive_binding_uses_the_reader(moved):
    from live_contentops import destination_transport_registry_v1 as registry

    manager = registry.DestinationReadinessManager()
    assert same(manager.env.get("TELEGRAM_BOT_TOKEN"), STORE["TELEGRAM_BOT_TOKEN"])
    assert "THREADS_USER_ACCESS_TOKEN" in manager.env
    for surface in ("THREADS_POST", "TELEGRAM_CHANNEL_POST", "DISCORD_ANNOUNCEMENT"):
        state = str(manager.passive_surface(surface).get("readiness_state"))
        assert state != "TRANSPORT_UNAVAILABLE", (surface, state)
    # FACEBOOK_PAGE_ID is in no source here, so the Page binding is still incomplete.
    assert str(manager.passive_surface("FACEBOOK_PAGE_POST").get("readiness_state")) == "TRANSPORT_UNAVAILABLE"


def test_presence_reports_see_moved_keys(moved):
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as eight
    from live_contentops import ai_provider_gate_v6, cloudinary_delivery_media_v1, direct_image_api_v1
    from live_contentops import linkedin_official_member_api_v1, neo_destination_handoff_v1
    from live_contentops import nine_router_provider_adapter_v2, video_platform_capability_matrix_v1
    from live_contentops.credential_hydration_gate import collect_env_key_presence
    from live_contentops.daily_app_launcher_v1 import build_credential_inventory

    presence = eight._capability_presence()
    assert presence["threads"] is True and presence["telegram"] is True and presence["youtube"] is True
    assert ai_provider_gate_v6.inspect_provider_credentials()["NINE_ROUTER_API_KEY"] is True
    assert cloudinary_delivery_media_v1.credential_presence() == {
        "CLOUDINARY_CLOUD_NAME": True, "CLOUDINARY_API_KEY": True, "CLOUDINARY_API_SECRET": True,
    }
    assert direct_image_api_v1.credential_presence() == {"AI_API_CHEAP_API_KEY": "PRESENT"}
    linkedin = linkedin_official_member_api_v1.env_name_presence()
    assert linkedin["LINKEDIN_CLIENT_ID"] is True and linkedin["LINKEDIN_CLIENT_SECRET"] is True
    projection = neo_destination_handoff_v1.destination_setup_projection(linkedin_root="C:/cc297-no-such-root")
    assert projection["threads"]["configuration_present"] is True
    assert projection["telegram"]["configuration_present"] is True
    nine = nine_router_provider_adapter_v2.credential_presence()
    assert nine["NINE_ROUTER_API_KEY"] != nine["NINE_ROUTER_BASE_URL"]   # key present, base URL absent
    matrix = video_platform_capability_matrix_v1.build_video_capability_matrix()
    assert isinstance(matrix, dict)
    rows = {row["variable"]: row["state"] for row in build_credential_inventory()}
    assert rows["THREADS_USER_ACCESS_TOKEN"] == "PRESENT"
    assert rows["TELEGRAM_BOT_TOKEN"] == "PRESENT"
    assert rows["THREADS_APP_SECRET"] == "MISSING"
    hydration = collect_env_key_presence("C:/cc297-no-such-repo", include_process_env=True)
    assert hydration["TELEGRAM_BOT_TOKEN"] is True and hydration["YOUTUBE_REFRESH_TOKEN"] is True


def test_key_reads_on_the_posting_paths(moved):
    from live_contentops import destination_performance_observer_v1 as observer
    from live_contentops import direct_image_api_v1, tiktok_local_desktop_oauth_pkce_v1

    assert same(observer._meta_token("FACEBOOK_PAGE_ACCESS_TOKEN", "META_ACCESS_TOKEN"), STORE["FACEBOOK_PAGE_ACCESS_TOKEN"])
    assert same(observer._meta_token("THREADS_USER_ACCESS_TOKEN", "THREADS_ACCESS_TOKEN"), STORE["THREADS_USER_ACCESS_TOKEN"])
    assert same(reader.read_secret(direct_image_api_v1.ENV_API_KEY), STORE["AI_API_CHEAP_API_KEY"])
    # No TikTok key is in any source here, so the read fails by its configuration code, never a value.
    with pytest.raises(tiktok_local_desktop_oauth_pkce_v1.TikTokOAuthError) as caught:
        tiktok_local_desktop_oauth_pkce_v1.read_approved_credentials()
    assert str(caught.value) == "REQUIRED_CONFIGURATION_ABSENT"


def test_launcher_guard_refuses_output_holding_a_stored_value(moved):
    from live_contentops import daily_app_launcher_v1 as launcher

    with pytest.raises(launcher.LauncherError) as caught:
        launcher._redaction_guard(f"summary {STORE['CLOUDINARY_API_SECRET']} end", {})
    assert "CLOUDINARY_API_SECRET" in str(caught.value)
    assert STORE["CLOUDINARY_API_SECRET"] not in str(caught.value)
    assert launcher._redaction_guard("summary with names only: CLOUDINARY_API_SECRET=PRESENT", {})


def test_explicit_mappings_still_win_for_injected_callers(moved):
    from live_contentops import cloudinary_delivery_media_v1, direct_image_api_v1
    from live_contentops import destination_transport_registry_v1 as registry

    assert cloudinary_delivery_media_v1.credential_presence({}) == {
        "CLOUDINARY_CLOUD_NAME": False, "CLOUDINARY_API_KEY": False, "CLOUDINARY_API_SECRET": False,
    }
    assert direct_image_api_v1.credential_presence({}) == {"AI_API_CHEAP_API_KEY": "MISSING"}
    assert registry.DestinationReadinessManager(env={}).env == {}
