from __future__ import annotations

import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from live_contentops.destination_transport_registry_v1 import (
    DestinationReadinessManager,
    registration_for_destination,
)
from live_contentops.linkedin_official_member_api_v1 import (
    CALLBACK_HOST,
    CALLBACK_PATH,
    CALLBACK_PORT,
    CALLBACK_URI,
    TOKEN_STORE_BINDING,
    TRANSPORT_VERSION,
    LinkedInAmbiguousWriteError,
    LinkedInOfficialApiError,
    LinkedInOfficialMemberApiTransportV1,
    WindowsDpapiTokenStore,
    authorize_interactively,
    build_authorization_url,
    build_linkedin_ugc_post_payload,
)
from live_contentops.publication_coordinator_v1 import (
    CanonicalDestinationTransportRuntimeV1,
    normalize_readback_result,
)


class _Response:
    def __init__(self, status: int, payload: dict | None = None, headers: dict | None = None):
        self.status = status
        self.payload = payload or {}
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def getcode(self):
        return self.status

    def read(self):
        return json.dumps(self.payload).encode()


def _test_store(root: Path) -> WindowsDpapiTokenStore:
    return WindowsDpapiTokenStore(
        root,
        protect=lambda value: b"protected:" + value[::-1],
        unprotect=lambda value: value.removeprefix(b"protected:")[::-1],
    )


def _metadata(*, expires_at: datetime, scopes=None):
    return {
        "schema_version": "contentops.linkedin_official_member_api_auth_metadata.v1",
        "auth_state": "READY_OFFICIAL_MEMBER_API",
        "granted_scopes": scopes or ["openid", "profile", "w_member_social"],
        "authorized_at_utc": "2026-08-13T00:00:00Z",
        "access_token_expires_at_utc": expires_at.isoformat().replace("+00:00", "Z"),
        "refresh_token_available": False,
        "token_store_binding": TOKEN_STORE_BINDING,
        "member_identity": {
            "subject": "member-123",
            "person_urn": "urn:li:person:member-123",
            "display_name": "Jim Pham",
        },
        "readback_capability": "READBACK_CAPABILITY_LIMITED",
    }


def test_authorization_url_is_official_and_never_contains_client_secret():
    url = build_authorization_url(client_id="public-id", state="cryptographic-state")
    parsed = urllib.parse.urlsplit(url)
    values = urllib.parse.parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "www.linkedin.com"
    assert values["redirect_uri"] == [CALLBACK_URI]
    assert values["state"] == ["cryptographic-state"]
    assert set(values["scope"][0].split()) == {"openid", "profile", "w_member_social"}
    assert "secret" not in values


def test_secure_store_roundtrip_keeps_secret_out_of_metadata(tmp_path):
    store = _test_store(tmp_path)
    metadata = _metadata(expires_at=datetime.now(timezone.utc) + timedelta(days=30))
    store.write({"access_token": "private-access", "refresh_token": None}, metadata)
    assert store.read_credentials()["access_token"] == "private-access"
    assert store.read_metadata()["refresh_token_available"] is False
    assert b"private-access" not in store.secret_path.read_bytes()
    assert "private-access" not in store.metadata_path.read_text(encoding="utf-8")


def test_readiness_expiry_states_are_sanitized_and_local_only(tmp_path):
    fixed = datetime(2026, 8, 13, tzinfo=timezone.utc)
    store = _test_store(tmp_path)
    store.write({"access_token": "private", "refresh_token": None}, _metadata(expires_at=fixed + timedelta(days=30)))
    transport = LinkedInOfficialMemberApiTransportV1(token_store=store, now=lambda: fixed)
    ready = transport.readiness()
    assert ready["state"] == "READY_OFFICIAL_MEMBER_API"
    assert ready["authenticated"] is True
    assert ready["days_remaining"] == 30
    assert ready["safe_identity"] == "Jim Pham"
    assert "token" not in json.dumps(ready).casefold()

    store.write({"access_token": "private", "refresh_token": None}, _metadata(expires_at=fixed + timedelta(days=3)))
    assert transport.readiness()["state"] == "TOKEN_EXPIRING"
    store.write({"access_token": "private", "refresh_token": None}, _metadata(expires_at=fixed - timedelta(seconds=1)))
    assert transport.readiness()["state"] == "REAUTH_REQUIRED"


def test_oauth_state_mismatch_fails_closed_without_code_exchange(tmp_path):
    env = {
        "LINKEDIN_CLIENT_ID": "public-id",
        "LINKEDIN_CLIENT_SECRET": "private-secret",
        "LINKEDIN_OAUTH_REDIRECT_URI": CALLBACK_URI,
    }
    provider_called = False

    def provider(_request, **_kwargs):
        nonlocal provider_called
        provider_called = True
        raise AssertionError("state mismatch must stop before exchange")

    def browser(url):
        del url
        def callback():
            try:
                urllib.request.urlopen(
                    f"http://{CALLBACK_HOST}:{CALLBACK_PORT}{CALLBACK_PATH}?state=wrong&code=never-log-this",
                    timeout=5,
                )
            except urllib.error.HTTPError:
                pass
        threading.Thread(target=callback, daemon=True).start()
        return True

    with pytest.raises(LinkedInOfficialApiError, match="OAUTH_STATE_MISMATCH"):
        authorize_interactively(
            env=env, auth_root=tmp_path, timeout_seconds=5,
            browser_opener=browser, opener=provider,
        )
    assert provider_called is False


def test_oauth_scope_product_error_is_classified_without_exchange(tmp_path):
    env = {
        "LINKEDIN_CLIENT_ID": "public-id",
        "LINKEDIN_CLIENT_SECRET": "private-secret",
        "LINKEDIN_OAUTH_REDIRECT_URI": CALLBACK_URI,
    }
    def browser(url):
        state = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["state"][0]
        def callback():
            try:
                urllib.request.urlopen(
                    f"http://{CALLBACK_HOST}:{CALLBACK_PORT}{CALLBACK_PATH}?"
                    + urllib.parse.urlencode({"state": state, "error": "invalid_scope"}),
                    timeout=5,
                )
            except urllib.error.HTTPError:
                pass
        threading.Thread(target=callback, daemon=True).start()
        return True
    with pytest.raises(LinkedInOfficialApiError, match="OAUTH_SCOPE_PRODUCT_ACCESS_UNAVAILABLE"):
        authorize_interactively(
            env=env, timeout_seconds=5, browser_opener=browser,
            opener=lambda *_args, **_kwargs: pytest.fail("scope error must not exchange"),
            token_store=_test_store(tmp_path),
        )


def test_oauth_exchange_identity_and_refresh_absence_are_persisted(tmp_path):
    env = {
        "LINKEDIN_CLIENT_ID": "public-id",
        "LINKEDIN_CLIENT_SECRET": "private-secret",
        "LINKEDIN_OAUTH_REDIRECT_URI": CALLBACK_URI,
    }
    store = _test_store(tmp_path)
    requests = []

    def provider(request, **_kwargs):
        requests.append(request)
        if request.full_url.endswith("/accessToken"):
            return _Response(200, {
                "access_token": "provider-access-token",
                "expires_in": 3600,
                "scope": "openid profile w_member_social",
            })
        return _Response(200, {"sub": "member-123", "name": "Jim Pham"})

    def browser(url):
        state = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["state"][0]
        def callback():
            urllib.request.urlopen(
                f"http://{CALLBACK_HOST}:{CALLBACK_PORT}{CALLBACK_PATH}?"
                + urllib.parse.urlencode({"state": state, "code": "authorization-code"}),
                timeout=5,
            ).read()
        threading.Thread(target=callback, daemon=True).start()
        return True

    result = authorize_interactively(
        env=env, timeout_seconds=5, browser_opener=browser,
        opener=provider, token_store=store,
    )
    assert result["status"] == "READY_OFFICIAL_MEMBER_API"
    assert result["access_token_issued"] is True
    assert result["refresh_token_issued"] is False
    assert result["member_identity"]["person_urn"] == "urn:li:person:member-123"
    assert store.read_metadata()["refresh_token_available"] is False
    assert store.read_credentials()["access_token"] == "provider-access-token"
    assert len(requests) == 2


def test_identity_mismatch_is_a_hard_stop(tmp_path):
    env = {
        "LINKEDIN_CLIENT_ID": "public-id",
        "LINKEDIN_CLIENT_SECRET": "private-secret",
        "LINKEDIN_OAUTH_REDIRECT_URI": CALLBACK_URI,
    }
    def provider(request, **_kwargs):
        if request.full_url.endswith("/accessToken"):
            return _Response(200, {"access_token": "private", "expires_in": 3600, "scope": "openid profile w_member_social"})
        return _Response(200, {"sub": "wrong", "name": "Another Member"})
    def browser(url):
        state = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["state"][0]
        threading.Thread(target=lambda: urllib.request.urlopen(
            f"http://{CALLBACK_HOST}:{CALLBACK_PORT}{CALLBACK_PATH}?" + urllib.parse.urlencode({"state": state, "code": "code"}),
            timeout=5,
        ).read(), daemon=True).start()
        return True
    with pytest.raises(LinkedInOfficialApiError, match="IDENTITY_MISMATCH"):
        authorize_interactively(env=env, timeout_seconds=5, browser_opener=browser, opener=provider, token_store=_test_store(tmp_path))


def test_locked_native_package_maps_deterministically():
    intent = {"payload": "Exact LinkedIn native package https://capitalchronicle.substack.com/p/story"}
    first = build_linkedin_ugc_post_payload(intent, person_urn="urn:li:person:member-123")
    second = build_linkedin_ugc_post_payload(intent, person_urn="urn:li:person:member-123")
    assert first == second
    assert first["author"] == "urn:li:person:member-123"
    assert first["lifecycleState"] == "PUBLISHED"
    assert first["visibility"]["com.linkedin.ugc.MemberNetworkVisibility"] == "PUBLIC"
    assert first["specificContent"]["com.linkedin.ugc.ShareContent"]["shareCommentary"]["text"] == intent["payload"]


def test_transport_contract_captures_official_object_id_and_limits_readback(tmp_path):
    now = datetime.now(timezone.utc)
    store = _test_store(tmp_path)
    store.write({"access_token": "private", "refresh_token": None}, _metadata(expires_at=now + timedelta(days=30)))
    seen = []
    def provider(request, **_kwargs):
        seen.append(request)
        return _Response(201, headers={"X-RestLi-Id": "urn:li:share:123"})
    transport = LinkedInOfficialMemberApiTransportV1(token_store=store, opener=provider)
    published = transport.publish(
        intent={"payload": "Exact native package"},
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT"},
    )
    assert published["public_object_id"] == "urn:li:share:123"
    assert published["adapter_version"] == TRANSPORT_VERSION
    request_body = json.loads(seen[0].data)
    assert request_body["author"] == "urn:li:person:member-123"
    readback = transport.readback(
        public_object_id=published["public_object_id"],
        public_object_url=published["public_object_url"], intent={},
    )
    assert readback["status"] == "READBACK_CAPABILITY_LIMITED"
    assert readback["write_exists"] is True
    assert readback["verified"] is False
    normalized = normalize_readback_result(readback, public_object_id="urn:li:share:123")
    assert normalized["verified"] is False
    assert normalized["write_exists"] is True
    assert len(seen) == 1


def test_strict_readback_outcomes_are_exact_when_restricted_scope_is_granted(tmp_path):
    now = datetime.now(timezone.utc)
    store = _test_store(tmp_path)
    store.write(
        {"access_token": "private", "refresh_token": None},
        _metadata(
            expires_at=now + timedelta(days=30),
            scopes=["openid", "profile", "w_member_social", "r_member_social"],
        ),
    )
    confirmed = LinkedInOfficialMemberApiTransportV1(
        token_store=store,
        opener=lambda *_args, **_kwargs: _Response(200, {"id": "urn:li:share:123"}),
    ).readback(public_object_id="urn:li:share:123", public_object_url=None, intent={})
    assert confirmed["status"] == "CONFIRMED"
    assert confirmed["verified"] is True

    def absent(request, **_kwargs):
        raise urllib.error.HTTPError(request.full_url, 404, "not found", {}, None)
    missing = LinkedInOfficialMemberApiTransportV1(
        token_store=store, opener=absent,
    ).readback(public_object_id="urn:li:share:missing", public_object_url=None, intent={})
    assert missing == {"status": "ABSENT_SAFE_TO_RETRY", "verified": False, "write_absent": True}


def test_timeout_after_crossing_write_boundary_is_unknown_write(tmp_path):
    now = datetime.now(timezone.utc)
    store = _test_store(tmp_path)
    store.write({"access_token": "private", "refresh_token": None}, _metadata(expires_at=now + timedelta(days=30)))
    transport = LinkedInOfficialMemberApiTransportV1(
        token_store=store,
        opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(urllib.error.URLError("timeout")),
    )
    with pytest.raises(LinkedInAmbiguousWriteError, match="UNKNOWN_WRITE"):
        transport.publish(
            intent={"payload": "Exact native package"},
            authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT"},
        )


def test_registry_readiness_and_runtime_never_fall_back_to_cdp(tmp_path):
    class FakeTransport:
        def readiness(self):
            return {
                "state": "READY_OFFICIAL_MEMBER_API", "authenticated": True,
                "safe_identity": "Jim Pham", "expiry_at_utc": "2026-09-13T00:00:00Z",
                "days_remaining": 31, "readback_capability": "READBACK_CAPABILITY_LIMITED",
                "secure_store_binding": TOKEN_STORE_BINDING,
            }
        def publish(self, **_kwargs):
            return {"status": "SUCCESS", "id": "urn:li:share:1"}
        def readback(self, **_kwargs):
            return {"status": "READBACK_CAPABILITY_LIMITED", "verified": False}
    official = FakeTransport()
    row = DestinationReadinessManager(env={}, linkedin_transport=official).probe_surface("LINKEDIN_POST")
    assert row["readiness_state"] == "READY_NON_BROWSER_BINDING"
    assert row["sanitized_detail"]["official_api_state"] == "READY_OFFICIAL_MEMBER_API"
    assert row["transport_type"] == "OFFICIAL_MEMBER_API"
    assert row["probe_kind"] == "OFFICIAL_MEMBER_API_LOCAL_AUTH_METADATA"
    assert row["sanitized_detail"]["cdp_navigation_performed"] is False
    assert registration_for_destination("linkedin").publishing_port is None

    runtime = CanonicalDestinationTransportRuntimeV1(linkedin_transport=official)
    result = runtime.publish(destination="linkedin", intent={}, authorization_context={})
    assert result["id"] == "urn:li:share:1"
    assert "edge" not in registration_for_destination("linkedin").adapter.casefold()


def test_historical_linkedin_cdp_entrypoints_are_unreachable(monkeypatch):
    import live_contentops.edge_cdp_publishing_adapter_v1 as adapter

    monkeypatch.setattr(
        adapter,
        "canonical_edge_page",
        lambda *_args, **_kwargs: pytest.fail("retired LinkedIn CDP entrypoint navigated Edge"),
    )
    published = adapter.publish_linkedin_post_via_edge(cdp_port=9223, text="never publish")
    readback = adapter.readback_linkedin_post_via_edge(
        cdp_port=9223, expected_text="never navigate", canonical_url="https://example.test",
    )
    assert published["status"] == "BLOCKED_LINKEDIN_CDP_TRANSPORT_RETIRED"
    assert published["browser_write_performed"] is False
    assert readback["status"] == "READBACK_CAPABILITY_LIMITED"
    assert readback["browser_navigation_performed"] is False
