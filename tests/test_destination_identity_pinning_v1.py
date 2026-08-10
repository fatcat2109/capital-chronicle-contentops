from __future__ import annotations

import pytest

import live_contentops.destination_transport_registry_v1 as registry
from live_contentops.destination_transport_registry_v1 import (
    DestinationReadinessManager,
    TIER1_SURFACES,
    canonical_transport_registry,
)
from tests.test_publication_coordinator_v1 import _coordinator, _plan


def _ready_edge(
    monkeypatch, observations, *, youtube_identity_verified=False,
    youtube_canonical_channel_id="UCcanonical",
):
    import live_contentops.edge_cdp_publishing_adapter_v1 as adapter
    import live_contentops.publishing_profile_registry_v1 as profiles

    monkeypatch.setattr(
        profiles,
        "browser_doctor",
        lambda **_kwargs: {"status": "READY_TO_ATTACH", "recommended_cdp_port": 9223},
    )
    monkeypatch.setattr(
        adapter,
        "probe_authenticated_platform_session",
        lambda _port, key: dict(observations[key]),
    )
    monkeypatch.setattr(
        adapter,
        "probe_youtube_community_surface_via_edge",
        lambda **_kwargs: {
            "channel_identity_verified": youtube_identity_verified,
            "canonical_channel_id": youtube_canonical_channel_id,
        },
    )


def test_registry_contains_owner_pins_without_changing_transport_routing():
    packet = canonical_transport_registry()
    expected_routing = {
        "SUBSTACK_ARTICLE": ("EDGE_CDP", 9223),
        "X_THREAD": ("EDGE_CDP", 9223),
        "LINKEDIN_POST": ("EDGE_CDP", 9223),
        "YOUTUBE_COMMUNITY_POST": ("EDGE_CDP", 9223),
        "TELEGRAM_CHANNEL_POST": ("BOT_API", None),
        "DISCORD_ANNOUNCEMENT": ("WEBHOOK_API", None),
        "FACEBOOK_PAGE_POST": ("META_GRAPH_API", None),
        "INSTAGRAM_BUSINESS_POST": ("META_GRAPH_API", None),
        "THREADS_POST": ("THREADS_API", None),
    }
    rows = {row["surface"]: row for row in packet["surfaces"]}
    assert packet["identity_authority_version"] == registry.IDENTITY_AUTHORITY_VERSION
    assert packet["runtime_binding_is_identity_authority"] is False
    assert packet["silent_transport_fallback_allowed"] is False
    assert packet["publishing_cdp_port"] == 9223
    assert packet["ingestion_only_cdp_port"] == 9222
    assert packet["chrome_publishing_allowed"] is False
    for surface in TIER1_SURFACES:
        row = rows[surface]
        assert any((row["expected_stable_id"], row["expected_public_handle"], row["expected_domain"]))
        assert (row["transport_type"], row["publishing_port"]) == expected_routing[surface]
    assert rows["SUBSTACK_ARTICLE"]["expected_domain"] == "capitalchronicle.substack.com"
    assert rows["DISCORD_ANNOUNCEMENT"]["expected_stable_id"] == "1519311669216673802"
    assert rows["FACEBOOK_PAGE_POST"]["expected_stable_id"] == "106091951705748"


@pytest.mark.parametrize(
    "domain,expected",
    [
        ("capitalchronicle.substack.com", "READY_AUTHENTICATED"),
        ("another-newsletter.substack.com", "IDENTITY_MISMATCH"),
    ],
)
def test_cases_a_b_substack_requires_exact_publication(monkeypatch, domain, expected):
    _ready_edge(monkeypatch, {
        "substack": {"authenticated": True, "page_domain": domain, "login_control_detected": False},
    })
    row = DestinationReadinessManager(env={}).probe_surface("SUBSTACK_ARTICLE")
    assert row["readiness_state"] == expected
    assert row["write_eligible"] is (expected == "READY_AUTHENTICATED")


@pytest.mark.parametrize(
    "username,expected",
    [("CapitalChronicle", "READY_NON_BROWSER_BINDING"), ("WrongCapitalChannel", "IDENTITY_MISMATCH")],
)
def test_cases_c_d_telegram_requires_owner_handle(monkeypatch, username, expected):
    def fake_get(url, **_kwargs):
        if url.endswith("/getMe"):
            return {"ok": True, "result": {"id": "bot-1"}}
        return {"ok": True, "result": {"id": "-100999", "username": username}}

    monkeypatch.setattr(registry, "_json_get", fake_get)
    manager = DestinationReadinessManager(env={
        "TELEGRAM_BOT_TOKEN": "fixture-token",
        "TELEGRAM_TARGET_CHAT_ID": "-100999",
    })
    row = manager.probe_surface("TELEGRAM_CHANNEL_POST")
    assert row["readiness_state"] == expected
    assert row["write_eligible"] is (expected == "READY_NON_BROWSER_BINDING")


def test_case_e_discord_wrong_valid_webhook_channel_is_mismatch(monkeypatch):
    monkeypatch.setattr(registry, "_json_get", lambda *_args, **_kwargs: {
        "id": "valid-webhook", "channel_id": "1519311669216671782",
    })
    row = DestinationReadinessManager(env={
        "DISCORD_WEBHOOK_URL": "https://fixture.invalid/webhook",
        "DISCORD_CHANNEL_ID": "1519311669216671782",
    }).probe_surface("DISCORD_ANNOUNCEMENT")
    assert row["readiness_state"] == "IDENTITY_MISMATCH"
    assert row["write_eligible"] is False


@pytest.mark.parametrize(
    "surface,env,provider",
    [
        (
            "FACEBOOK_PAGE_POST",
            {"FACEBOOK_PAGE_ID": "wrong-page", "FACEBOOK_PAGE_ACCESS_TOKEN": "fixture-token"},
            {"id": "wrong-page", "name": "Wrong Publication"},
        ),
        (
            "INSTAGRAM_BUSINESS_POST",
            {"INSTAGRAM_BUSINESS_ACCOUNT_ID": "wrong-ig", "INSTAGRAM_ACCESS_TOKEN": "fixture-token"},
            {"id": "wrong-ig", "username": "wrong.publication"},
        ),
        (
            "THREADS_POST",
            {"THREADS_USER_ID": "wrong-threads", "THREADS_ACCESS_TOKEN": "fixture-token"},
            {"id": "wrong-threads", "username": "wrong.publication"},
        ),
    ],
)
def test_cases_f_g_h_graph_env_id_equal_provider_id_is_not_authority(
    monkeypatch, surface, env, provider,
):
    monkeypatch.setattr(registry, "_json_get", lambda *_args, **_kwargs: provider)
    row = DestinationReadinessManager(env=env).probe_surface(surface)
    assert row["readiness_state"] == "IDENTITY_MISMATCH"
    assert row["identity_match"] is False
    assert row["write_eligible"] is False


@pytest.mark.parametrize(
    "surface,key,identity",
    [
        ("X_THREAD", "x", "@WrongCapitalAccount"),
        ("LINKEDIN_POST", "linkedin", "linkedin:wrong-owner"),
    ],
)
def test_cases_i_j_wrong_authenticated_browser_account_is_mismatch(
    monkeypatch, surface, key, identity,
):
    _ready_edge(monkeypatch, {
        key: {"authenticated": True, "destination_identity": identity, "login_control_detected": False},
    })
    row = DestinationReadinessManager(env={}).probe_surface(surface)
    assert row["readiness_state"] == "IDENTITY_MISMATCH"
    assert row["write_eligible"] is False


def test_case_k_wrong_authenticated_youtube_channel_is_mismatch(monkeypatch):
    _ready_edge(monkeypatch, {
        "youtube": {
            "authenticated": True,
            "destination_identity": "@WrongChannel",
            "destination_stable_id": "UCwrong",
            "login_control_detected": False,
        },
    }, youtube_identity_verified=False)
    row = DestinationReadinessManager(env={}).probe_surface("YOUTUBE_COMMUNITY_POST")
    assert row["readiness_state"] == "IDENTITY_MISMATCH"
    assert row["write_eligible"] is False


def test_youtube_public_handle_page_cannot_self_authorize_wrong_studio_channel(monkeypatch):
    _ready_edge(monkeypatch, {
        "youtube": {
            "authenticated": True,
            "destination_stable_id": "UCwrong",
            "login_control_detected": False,
        },
    }, youtube_identity_verified=True, youtube_canonical_channel_id="UCcanonical")
    row = DestinationReadinessManager(env={}).probe_surface("YOUTUBE_COMMUNITY_POST")
    assert row["readiness_state"] == "IDENTITY_MISMATCH"
    assert row["write_eligible"] is False


@pytest.mark.parametrize("readiness", ["IDENTITY_MISMATCH", "REAUTH_REQUIRED", "AUTH_INVALID"])
def test_nonready_identity_or_auth_state_never_calls_publisher(tmp_path, readiness):
    _store, transport, coordinator = _coordinator(
        tmp_path, readiness={"telegram": readiness},
    )
    result = coordinator.execute_plan("work-1", _plan("telegram"))
    assert result["per_destination"]["telegram"]["status"] == readiness
    assert transport.publish_calls == []
