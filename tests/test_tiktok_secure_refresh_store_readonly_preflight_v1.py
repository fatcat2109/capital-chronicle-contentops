from __future__ import annotations

import io
import json
import subprocess
import sys
import urllib.error
import uuid
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Mapping

import pytest

from live_contentops import tiktok_local_desktop_oauth_pkce_v1 as oauth
from live_contentops import tiktok_secure_refresh_store_readonly_preflight_v1 as secure


ROOT = Path(__file__).resolve().parents[1]


def _secret(label: str) -> str:
    return "TEST-ONLY-" + label + "-" + ("Q" * 37)


def _session(
    *,
    access_token: str | None = None,
    refresh_token: str | None = None,
    open_id: str | None = None,
    scopes: tuple[str, ...] = oauth.REQUIRED_SCOPES,
) -> oauth.TikTokTokenSession:
    return oauth.TikTokTokenSession(
        access_token=access_token or _secret("access-token"),
        refresh_token=refresh_token or _secret("refresh-token"),
        open_id=open_id or _secret("open-id"),
        granted_scopes=scopes,
        expires_in=86400,
        refresh_expires_in=31536000,
        token_type="Bearer",
    )


def _user_info_payload(
    open_id: str,
    *,
    display_name: str | None = "Capital Chronicle Test",
) -> dict[str, Any]:
    user: dict[str, Any] = {"open_id": open_id}
    if display_name is not None:
        user["display_name"] = display_name
    return {"data": {"user": user}, "error": {"code": "ok", "message": ""}}


class FakeCredentialBackend:
    def __init__(self) -> None:
        self.records: dict[str, secure.CredentialRecord] = {}
        self.write_calls = 0
        self.read_calls = 0
        self.delete_calls = 0
        self.fail_write = False
        self.fail_read = False
        self.fail_delete = False
        self.corrupt_read = False

    def write(self, target: str, *, username: str, secret: str) -> None:
        self.write_calls += 1
        if self.fail_write:
            raise secure.TikTokSecureSessionError("CREDENTIAL_WRITE_FAILED")
        self.records[target] = secure.CredentialRecord(username=username, secret=secret)

    def read(self, target: str) -> secure.CredentialRecord | None:
        self.read_calls += 1
        if self.fail_read:
            raise secure.TikTokSecureSessionError("CREDENTIAL_READ_FAILED")
        if self.corrupt_read:
            raise secure.TikTokSecureSessionError("CREDENTIAL_RECORD_CORRUPT")
        return self.records.get(target)

    def delete(self, target: str) -> None:
        self.delete_calls += 1
        if self.fail_delete:
            raise secure.TikTokSecureSessionError("CREDENTIAL_DELETE_FAILED")
        self.records.pop(target, None)


class UnavailableCredentialBackend:
    def write(self, target: str, *, username: str, secret: str) -> None:
        raise secure.TikTokSecureSessionError("CREDENTIAL_MANAGER_UNAVAILABLE")

    def read(self, target: str) -> secure.CredentialRecord | None:
        raise secure.TikTokSecureSessionError("CREDENTIAL_MANAGER_UNAVAILABLE")

    def delete(self, target: str) -> None:
        raise secure.TikTokSecureSessionError("CREDENTIAL_MANAGER_UNAVAILABLE")


class FakeUserInfoTransport:
    def __init__(self, payload: Mapping[str, Any] | None = None) -> None:
        self.payload = dict(payload or {})
        self.calls: list[tuple[str, tuple[str, ...], str, float]] = []

    def get_user_info(
        self,
        endpoint: str,
        *,
        fields: tuple[str, ...],
        access_token: str,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        self.calls.append((endpoint, fields, access_token, timeout_seconds))
        return dict(self.payload)


class FakeTokenTransport:
    def __init__(
        self,
        payload: Mapping[str, Any] | None = None,
        *,
        error: oauth.TikTokOAuthError | None = None,
    ) -> None:
        self.payload = dict(payload or {})
        self.error = error
        self.calls: list[tuple[str, dict[str, str], float]] = []

    def post_form(
        self,
        endpoint: str,
        form: Mapping[str, str],
        *,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        self.calls.append((endpoint, dict(form), timeout_seconds))
        if self.error is not None:
            raise self.error
        return dict(self.payload)


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200) -> None:
        self.body = body
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def getcode(self) -> int:
        return self.status

    def read(self) -> bytes:
        return self.body


def _token_payload(session: oauth.TikTokTokenSession) -> dict[str, Any]:
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "open_id": session.open_id,
        "scope": ",".join(session.granted_scopes),
        "expires_in": session.expires_in,
        "refresh_expires_in": session.refresh_expires_in,
        "token_type": session.token_type,
    }


def test_import_has_no_environment_credential_or_network_side_effect() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import live_contentops."
                "tiktok_secure_refresh_store_readonly_preflight_v1; print('IMPORTED')"
            ),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "IMPORTED"
    assert completed.stderr == ""


def test_fake_store_write_read_replace_read_delete_absent() -> None:
    backend = FakeCredentialBackend()
    store = secure.TikTokRefreshCredentialStore(backend)
    original = secure.RefreshCredentialSession(
        refresh_token=_secret("old-refresh"),
        open_id=_secret("open-id"),
    )
    store.store_refresh_session(original)
    assert store.load_refresh_session() == original

    rotated = _session(
        refresh_token=_secret("new-refresh"),
        open_id=original.open_id,
    )
    replacement = store.replace_rotated_refresh_session(original, rotated)
    assert replacement.refresh_token == rotated.refresh_token
    assert store.load_refresh_session() == replacement
    assert backend.write_calls == 2

    store.delete_refresh_session()
    assert backend.records == {}
    with pytest.raises(
        secure.TikTokSecureSessionError, match="MISSING_REFRESH_CREDENTIAL"
    ):
        store.load_refresh_session()


def test_same_refresh_token_does_not_rewrite_credential() -> None:
    backend = FakeCredentialBackend()
    store = secure.TikTokRefreshCredentialStore(backend)
    original = secure.RefreshCredentialSession(
        refresh_token=_secret("unchanged-refresh"),
        open_id=_secret("open-id"),
    )
    store.store_refresh_session(original)
    assert store.replace_rotated_refresh_session(
        original,
        _session(refresh_token=original.refresh_token, open_id=original.open_id),
    ) == original
    assert backend.write_calls == 1


def test_initial_store_refuses_to_overwrite_a_different_open_id() -> None:
    backend = FakeCredentialBackend()
    store = secure.TikTokRefreshCredentialStore(backend)
    original = secure.RefreshCredentialSession(
        refresh_token=_secret("original-refresh"),
        open_id=_secret("original-open-id"),
    )
    store.store_refresh_session(original)
    with pytest.raises(
        secure.TikTokSecureSessionError, match="IDENTITY_OPEN_ID_MISMATCH"
    ):
        store.store_refresh_session(
            secure.RefreshCredentialSession(
                refresh_token=_secret("other-refresh"),
                open_id=_secret("other-open-id"),
            )
        )
    assert backend.write_calls == 1
    assert backend.records[secure.CREDENTIAL_TARGET].secret == original.refresh_token


def test_readonly_identity_preflight_uses_exact_endpoint_fields_and_binding() -> None:
    session = _session()
    transport = FakeUserInfoTransport(_user_info_payload(session.open_id))
    result = secure.readonly_identity_preflight(session, transport=transport)
    assert result.open_id_match is True
    assert result.display_name_received is True
    assert transport.calls == [
        (
            secure.USER_INFO_ENDPOINT,
            ("open_id", "display_name"),
            session.access_token,
            oauth.DEFAULT_HTTP_TIMEOUT_SECONDS,
        )
    ]
    assert "username" not in transport.calls[0][1]


def test_urllib_user_info_transport_uses_get_and_transient_bearer_header() -> None:
    session = _session()
    requests: list[Any] = []

    def opener(request: Any, *, timeout: float) -> FakeResponse:
        requests.append((request, timeout))
        return FakeResponse(json.dumps(_user_info_payload(session.open_id)).encode("utf-8"))

    result = secure.readonly_identity_preflight(
        session,
        transport=secure.UrllibUserInfoTransport(opener=opener),
    )
    assert result.open_id_match is True
    request, timeout = requests[0]
    assert request.get_method() == "GET"
    assert request.full_url == secure.USER_INFO_ENDPOINT + "?fields=open_id%2Cdisplay_name"
    assert request.get_header("Authorization") == "Bearer " + session.access_token
    assert timeout == oauth.DEFAULT_HTTP_TIMEOUT_SECONDS


@pytest.mark.parametrize(
    ("payload", "classification"),
    [
        ({"data": {"user": {}}, "error": {"code": "ok"}}, "USER_INFO_OPEN_ID_MISSING"),
        ({"data": {}, "error": {"code": "ok"}}, "USER_INFO_RESPONSE_MALFORMED"),
        ({"data": {"user": {}}, "error": {"code": "denied"}}, "USER_INFO_API_ERROR"),
    ],
)
def test_user_info_response_failures_are_stable(
    payload: Mapping[str, Any], classification: str
) -> None:
    with pytest.raises(secure.TikTokSecureSessionError) as captured:
        secure.readonly_identity_preflight(
            _session(), transport=FakeUserInfoTransport(payload)
        )
    assert str(captured.value) == classification


def test_user_info_open_id_mismatch_blocks_before_initial_persistence() -> None:
    backend = FakeCredentialBackend()
    session = _session()
    with pytest.raises(
        secure.TikTokSecureSessionError, match="IDENTITY_OPEN_ID_MISMATCH"
    ):
        secure.persist_supervised_session_after_preflight(
            session,
            store=secure.TikTokRefreshCredentialStore(backend),
            user_info_transport=FakeUserInfoTransport(
                _user_info_payload(_secret("different-open-id"))
            ),
        )
    assert backend.write_calls == 0
    assert backend.records == {}


def test_user_info_http_and_malformed_json_fail_closed() -> None:
    http_transport = secure.UrllibUserInfoTransport(
        opener=lambda _request, timeout: (_ for _ in ()).throw(
            urllib.error.HTTPError("https://example.invalid", 401, "", {}, None)
        )
    )
    with pytest.raises(secure.TikTokSecureSessionError, match="USER_INFO_HTTP_ERROR"):
        secure.readonly_identity_preflight(_session(), transport=http_transport)

    malformed_transport = secure.UrllibUserInfoTransport(
        opener=lambda _request, timeout: FakeResponse(b"not-json")
    )
    with pytest.raises(
        secure.TikTokSecureSessionError,
        match="USER_INFO_RESPONSE_MALFORMED_JSON",
    ):
        secure.readonly_identity_preflight(_session(), transport=malformed_transport)


def test_missing_scope_and_incomplete_required_scopes_fail_closed() -> None:
    basic_missing = _session(scopes=("video.list", "video.upload"))
    with pytest.raises(secure.TikTokSecureSessionError, match="IDENTITY_SCOPE_MISSING"):
        secure.readonly_identity_preflight(
            basic_missing,
            transport=FakeUserInfoTransport(_user_info_payload(basic_missing.open_id)),
        )

    incomplete = _session(scopes=("user.info.basic",))
    with pytest.raises(
        secure.TikTokSecureSessionError, match="REQUIRED_SCOPES_INCOMPLETE"
    ):
        secure.persist_supervised_session_after_preflight(
            incomplete,
            store=secure.TikTokRefreshCredentialStore(FakeCredentialBackend()),
            user_info_transport=FakeUserInfoTransport(
                _user_info_payload(incomplete.open_id)
            ),
        )


def test_missing_corrupt_unavailable_and_read_write_cleanup_failures() -> None:
    missing_backend = FakeCredentialBackend()
    with pytest.raises(
        secure.TikTokSecureSessionError, match="MISSING_REFRESH_CREDENTIAL"
    ):
        secure.TikTokRefreshCredentialStore(missing_backend).load_refresh_session()

    corrupt_backend = FakeCredentialBackend()
    corrupt_backend.corrupt_read = True
    with pytest.raises(
        secure.TikTokSecureSessionError, match="CORRUPT_REFRESH_CREDENTIAL"
    ):
        secure.TikTokRefreshCredentialStore(corrupt_backend).load_refresh_session()

    read_backend = FakeCredentialBackend()
    read_backend.fail_read = True
    with pytest.raises(secure.TikTokSecureSessionError, match="CREDENTIAL_READ_FAILED"):
        secure.TikTokRefreshCredentialStore(read_backend).load_refresh_session()

    with pytest.raises(
        secure.TikTokSecureSessionError,
        match="CREDENTIAL_MANAGER_UNAVAILABLE",
    ):
        secure.TikTokRefreshCredentialStore(
            UnavailableCredentialBackend()
        ).load_refresh_session()

    write_backend = FakeCredentialBackend()
    write_backend.fail_write = True
    with pytest.raises(secure.TikTokSecureSessionError, match="CREDENTIAL_WRITE_FAILED"):
        secure.TikTokRefreshCredentialStore(write_backend).store_refresh_session(
            secure.RefreshCredentialSession(_secret("refresh"), _secret("open-id"))
        )

    delete_backend = FakeCredentialBackend()
    delete_backend.fail_delete = True
    with pytest.raises(secure.TikTokSecureSessionError, match="CREDENTIAL_DELETE_FAILED"):
        secure.TikTokRefreshCredentialStore(delete_backend).delete_refresh_session()

    if sys.platform != "win32":
        with pytest.raises(
            secure.TikTokSecureSessionError,
            match="CREDENTIAL_MANAGER_UNAVAILABLE",
        ):
            secure.WindowsCredentialManagerBackend()


def test_rotation_write_failure_preserves_old_credential_and_does_not_refresh_twice() -> None:
    backend = FakeCredentialBackend()
    store = secure.TikTokRefreshCredentialStore(backend)
    original = secure.RefreshCredentialSession(_secret("old-refresh"), _secret("open-id"))
    store.store_refresh_session(original)
    backend.fail_write = True
    refreshed = _session(
        refresh_token=_secret("rotated-refresh"),
        open_id=original.open_id,
    )
    token_transport = FakeTokenTransport(_token_payload(refreshed))
    with pytest.raises(
        secure.TikTokSecureSessionError,
        match="REFRESH_ROTATION_PERSISTENCE_FAILED",
    ):
        secure.refresh_stored_session_and_preflight(
            store=store,
            token_transport=token_transport,
            user_info_transport=FakeUserInfoTransport(
                _user_info_payload(refreshed.open_id)
            ),
            env={
                oauth.CLIENT_KEY_ENV: _secret("client-key"),
                oauth.CLIENT_SECRET_ENV: _secret("client-secret"),
            },
        )
    assert len(token_transport.calls) == 1
    assert backend.records[secure.CREDENTIAL_TARGET].secret == original.refresh_token


def test_refresh_open_id_mismatch_blocks_rotation() -> None:
    backend = FakeCredentialBackend()
    store = secure.TikTokRefreshCredentialStore(backend)
    stored = secure.RefreshCredentialSession(_secret("old-refresh"), _secret("open-id"))
    store.store_refresh_session(stored)
    refreshed = _session(
        refresh_token=_secret("rotated-refresh"),
        open_id=_secret("different-open-id"),
    )
    with pytest.raises(
        secure.TikTokSecureSessionError, match="IDENTITY_OPEN_ID_MISMATCH"
    ):
        secure.refresh_stored_session_and_preflight(
            store=store,
            token_transport=FakeTokenTransport(_token_payload(refreshed)),
            user_info_transport=FakeUserInfoTransport(
                _user_info_payload(refreshed.open_id)
            ),
            env={
                oauth.CLIENT_KEY_ENV: _secret("client-key"),
                oauth.CLIENT_SECRET_ENV: _secret("client-secret"),
            },
        )
    assert backend.write_calls == 1
    assert backend.records[secure.CREDENTIAL_TARGET].secret == stored.refresh_token


def test_refresh_http_malformed_response_and_missing_fake_environment_failures() -> None:
    backend = FakeCredentialBackend()
    store = secure.TikTokRefreshCredentialStore(backend)
    stored = secure.RefreshCredentialSession(_secret("refresh"), _secret("open-id"))
    store.store_refresh_session(stored)
    env = {
        oauth.CLIENT_KEY_ENV: _secret("client-key"),
        oauth.CLIENT_SECRET_ENV: _secret("client-secret"),
    }
    with pytest.raises(oauth.TikTokOAuthError, match="TOKEN_HTTP_ERROR"):
        secure.refresh_stored_session_and_preflight(
            store=store,
            token_transport=FakeTokenTransport(
                error=oauth.TikTokOAuthError("TOKEN_HTTP_ERROR")
            ),
            user_info_transport=FakeUserInfoTransport(),
            env=env,
        )
    with pytest.raises(oauth.TikTokOAuthError, match="TOKEN_RESPONSE_ACCESS_TOKEN_MISSING"):
        secure.refresh_stored_session_and_preflight(
            store=store,
            token_transport=FakeTokenTransport(
                {"refresh_token": _secret("refresh"), "open_id": stored.open_id}
            ),
            user_info_transport=FakeUserInfoTransport(),
            env=env,
        )
    with pytest.raises(oauth.TikTokOAuthError, match="REQUIRED_CONFIGURATION_ABSENT"):
        secure.refresh_stored_session_and_preflight(
            store=store,
            token_transport=FakeTokenTransport(),
            user_info_transport=FakeUserInfoTransport(),
            env={},
        )


def test_fake_supervised_then_stored_rotation_e2e_has_redacted_pass_receipts() -> None:
    backend = FakeCredentialBackend()
    store = secure.TikTokRefreshCredentialStore(backend)
    initial = _session()
    supervised_receipt = secure.persist_supervised_session_after_preflight(
        initial,
        store=store,
        user_info_transport=FakeUserInfoTransport(_user_info_payload(initial.open_id)),
    )
    assert supervised_receipt["oauth_success"] is True
    assert supervised_receipt["identity_preflight_success"] is True
    assert supervised_receipt["refresh_token_persisted"] is True
    assert supervised_receipt["access_token_persisted"] is False

    rotated = _session(
        access_token=_secret("refreshed-access-token"),
        refresh_token=_secret("rotated-refresh-token"),
        open_id=initial.open_id,
    )
    token_transport = FakeTokenTransport(_token_payload(rotated))
    stored_receipt = secure.refresh_stored_session_and_preflight(
        store=store,
        token_transport=token_transport,
        user_info_transport=FakeUserInfoTransport(
            _user_info_payload(rotated.open_id, display_name=None)
        ),
        env={
            oauth.CLIENT_KEY_ENV: _secret("client-key"),
            oauth.CLIENT_SECRET_ENV: _secret("client-secret"),
        },
    )
    assert stored_receipt["refresh_success"] is True
    assert stored_receipt["open_id_match"] is True
    assert stored_receipt["display_name_received"] is False
    assert store.load_refresh_session().refresh_token == rotated.refresh_token
    assert len(token_transport.calls) == 1


def test_secret_shaped_values_never_enter_output_strings_exceptions_or_receipts() -> None:
    client_secret = _secret("client-secret-private")
    access_token = _secret("access-token-private")
    refresh_token = _secret("refresh-token-private")
    rotated_token = _secret("rotated-refresh-token-private")
    open_id = _secret("open-id-private")
    initial = _session(
        access_token=access_token,
        refresh_token=refresh_token,
        open_id=open_id,
    )
    backend = FakeCredentialBackend()
    store = secure.TikTokRefreshCredentialStore(backend)
    stdout = io.StringIO()
    stderr = io.StringIO()
    strings: list[str] = []
    with redirect_stdout(stdout), redirect_stderr(stderr):
        receipt = secure.persist_supervised_session_after_preflight(
            initial,
            store=store,
            user_info_transport=FakeUserInfoTransport(_user_info_payload(open_id)),
        )
        stored = store.load_refresh_session()
        strings.extend((repr(stored), str(stored), repr(initial), str(initial)))
        backend.fail_write = True
        try:
            store.replace_rotated_refresh_session(
                stored,
                _session(refresh_token=rotated_token, open_id=open_id),
            )
        except secure.TikTokSecureSessionError as exc:
            strings.extend((repr(exc), str(exc)))
    combined = "\n".join(
        [stdout.getvalue(), stderr.getvalue(), json.dumps(receipt), *strings]
    )
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""
    for secret_value in (
        client_secret,
        access_token,
        refresh_token,
        rotated_token,
        open_id,
    ):
        assert secret_value not in combined


def test_secret_value_in_receipt_is_rejected_without_echoing_it() -> None:
    secret_value = _secret("receipt-leak")
    with pytest.raises(
        secure.TikTokSecureSessionError, match="SECRET_MATERIAL_IN_RECEIPT"
    ) as captured:
        secure.validate_redacted_receipt(
            {"result": "FAIL", "unsafe": secret_value},
            secret_values=(secret_value,),
        )
    assert secret_value not in str(captured.value)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Credential Manager only")
def test_windows_credential_manager_fake_roundtrip_and_cleanup() -> None:
    target = "CapitalChronicle.ContentOps/TikTok/Test/" + uuid.uuid4().hex
    backend = secure.WindowsCredentialManagerBackend()
    store = secure.TikTokRefreshCredentialStore(backend, target=target)
    original = secure.RefreshCredentialSession(
        _secret("native-old-refresh"),
        _secret("native-open-id"),
    )
    rotated = _session(
        refresh_token=_secret("native-new-refresh"),
        open_id=original.open_id,
    )
    cleanup_error: Exception | None = None
    try:
        store.store_refresh_session(original)
        assert store.load_refresh_session() == original
        replacement = store.replace_rotated_refresh_session(original, rotated)
        assert store.load_refresh_session() == replacement
    finally:
        try:
            store.delete_refresh_session()
            assert backend.read(target) is None
        except Exception as exc:  # pragma: no cover - machine-specific hard blocker
            cleanup_error = exc
    if cleanup_error is not None:
        pytest.fail(f"TEST_CREDENTIAL_CLEANUP_FAILED target={target}")
