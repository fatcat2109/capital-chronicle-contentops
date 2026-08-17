from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pytest

from live_contentops import tiktok_local_desktop_oauth_pkce_v1 as oauth
from live_contentops import tiktok_secure_refresh_store_readonly_preflight_v1 as secure
from scripts import run_tiktok_secure_persistence_oauth_readonly_preflight_v1 as cli


ROOT = Path(__file__).resolve().parents[1]
TEST_TARGET = "CapitalChronicle.ContentOps/TikTok/Test/supervised-cli-fixture"


def _secret(label: str) -> str:
    return "TEST-ONLY-CLI-" + label + "-" + ("R" * 31)


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


class FakeCredentialBackend:
    def __init__(self, events: list[str] | None = None) -> None:
        self.events = events if events is not None else []
        self.records: dict[str, secure.CredentialRecord] = {}
        self.read_calls = 0
        self.write_calls = 0
        self.delete_calls = 0
        self.fail_write = False

    def write(self, target: str, *, username: str, secret: str) -> None:
        self.events.append("store_write")
        self.write_calls += 1
        if self.fail_write:
            raise secure.TikTokSecureSessionError("CREDENTIAL_WRITE_FAILED")
        self.records[target] = secure.CredentialRecord(username=username, secret=secret)

    def read(self, target: str) -> secure.CredentialRecord | None:
        self.events.append("store_read")
        self.read_calls += 1
        return self.records.get(target)

    def delete(self, target: str) -> None:
        self.events.append("store_delete")
        self.delete_calls += 1
        self.records.pop(target, None)


class FakeUserInfoTransport:
    def __init__(
        self,
        open_id: str,
        *,
        events: list[str] | None = None,
        failure: str | None = None,
    ) -> None:
        self.open_id = open_id
        self.events = events if events is not None else []
        self.failure = failure
        self.calls = 0

    def get_user_info(
        self,
        endpoint: str,
        *,
        fields: tuple[str, ...],
        access_token: str,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        self.events.append("user_info")
        self.calls += 1
        if self.failure is not None:
            raise secure.TikTokSecureSessionError(self.failure)
        return {
            "data": {
                "user": {
                    "open_id": self.open_id,
                    "display_name": "Capital Chronicle Test",
                }
            },
            "error": {"code": "ok", "message": ""},
        }


class SentinelTransport:
    pass


def _store(
    backend: FakeCredentialBackend | None = None,
) -> tuple[secure.TikTokRefreshCredentialStore, FakeCredentialBackend]:
    active_backend = backend or FakeCredentialBackend()
    return (
        secure.TikTokRefreshCredentialStore(active_backend, target=TEST_TARGET),
        active_backend,
    )


def _receipt(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)


def test_cli_import_has_zero_runtime_side_effects() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import scripts."
                "run_tiktok_secure_persistence_oauth_readonly_preflight_v1; "
                "print('IMPORTED')"
            ),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "IMPORTED"
    assert completed.stderr == ""


def test_no_execution_flag_has_zero_env_store_oauth_or_network_access(
    capsys: pytest.CaptureFixture[str],
) -> None:
    store, backend = _store()
    calls = {"credentials": 0, "oauth": 0}

    def credential_reader(_env: Mapping[str, str] | None) -> oauth.TikTokAppCredentials:
        calls["credentials"] += 1
        raise AssertionError("credential reader must not run")

    def authorizer(*_args: Any, **_kwargs: Any) -> oauth.TikTokTokenSession:
        calls["oauth"] += 1
        raise AssertionError("OAuth must not run")

    result = cli.main(
        [],
        env={},
        store=store,
        token_transport=SentinelTransport(),
        user_info_transport=FakeUserInfoTransport(_secret("open-id")),
        credential_reader=credential_reader,
        oauth_authorizer=authorizer,
    )
    receipt = _receipt(capsys)
    assert result == 2
    assert receipt["result"] == cli.CONFIRMATION_REQUIRED
    assert receipt["refresh_token_persisted"] is False
    assert calls == {"credentials": 0, "oauth": 0}
    assert backend.read_calls == 0
    assert backend.write_calls == 0


def test_successful_fake_oauth_identity_store_flow_is_ordered_and_redacted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    events: list[str] = []
    backend = FakeCredentialBackend(events)
    store, _ = _store(backend)
    session = _session()
    controlled_env = {
        oauth.CLIENT_KEY_ENV: _secret("client-key"),
        oauth.CLIENT_SECRET_ENV: _secret("client-secret"),
    }

    def credential_reader(env: Mapping[str, str] | None) -> oauth.TikTokAppCredentials:
        events.append("credential_read")
        return oauth.read_approved_credentials(env)

    def authorizer(
        credentials: oauth.TikTokAppCredentials,
        *,
        transport: Any,
    ) -> oauth.TikTokTokenSession:
        events.append("oauth")
        assert credentials.client_key == controlled_env[oauth.CLIENT_KEY_ENV]
        assert isinstance(transport, SentinelTransport)
        return session

    result = cli.main(
        [cli.EXECUTION_FLAG],
        env=controlled_env,
        store=store,
        token_transport=SentinelTransport(),
        user_info_transport=FakeUserInfoTransport(
            session.open_id,
            events=events,
        ),
        credential_reader=credential_reader,
        oauth_authorizer=authorizer,
    )
    receipt = _receipt(capsys)
    assert result == 0
    assert set(receipt) == set(cli._SUCCESS_FIELDS)
    assert receipt == {
        "access_token_persisted": False,
        "content_posting_calls": 0,
        "credential_target": TEST_TARGET,
        "display_name_received": True,
        "environment_mutated": False,
        "identity_preflight_success": True,
        "media_uploads": 0,
        "open_id_match": True,
        "public_writes": 0,
        "refresh_token_persisted": True,
        "required_scopes_satisfied": True,
        "result": "TIKTOK_SECURE_REFRESH_AND_IDENTITY_PREFLIGHT_READY",
        "state_validated": True,
    }
    assert events == [
        "store_read",
        "credential_read",
        "oauth",
        "user_info",
        "store_read",
        "store_write",
        "store_read",
    ]
    record = backend.records[TEST_TARGET]
    assert record.secret == session.refresh_token
    assert record.username == session.open_id
    assert record.secret != session.access_token


def test_open_id_mismatch_and_user_info_failure_never_write(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for user_info in (
        FakeUserInfoTransport(_secret("different-open-id")),
        FakeUserInfoTransport(
            _secret("open-id"),
            failure="USER_INFO_HTTP_ERROR",
        ),
    ):
        store, backend = _store()
        session = _session(open_id=_secret("open-id"))
        result = cli.main(
            [cli.EXECUTION_FLAG],
            env={},
            store=store,
            token_transport=SentinelTransport(),
            user_info_transport=user_info,
            credential_reader=lambda _env: oauth.TikTokAppCredentials("key", "secret"),
            oauth_authorizer=lambda _credentials, **_kwargs: session,
        )
        receipt = _receipt(capsys)
        assert result == 2
        assert receipt["result"] in {
            "IDENTITY_OPEN_ID_MISMATCH",
            "USER_INFO_HTTP_ERROR",
        }
        assert backend.write_calls == 0
        assert backend.records == {}


def test_incomplete_scopes_and_oauth_failure_never_write(
    capsys: pytest.CaptureFixture[str],
) -> None:
    store, backend = _store()
    incomplete = _session(scopes=("user.info.basic",))
    result = cli.main(
        [cli.EXECUTION_FLAG],
        env={},
        store=store,
        token_transport=SentinelTransport(),
        user_info_transport=FakeUserInfoTransport(incomplete.open_id),
        credential_reader=lambda _env: oauth.TikTokAppCredentials("key", "secret"),
        oauth_authorizer=lambda _credentials, **_kwargs: incomplete,
    )
    assert result == 2
    assert _receipt(capsys)["result"] == "REQUIRED_SCOPES_INCOMPLETE"
    assert backend.write_calls == 0

    store, backend = _store()

    def failed_oauth(*_args: Any, **_kwargs: Any) -> oauth.TikTokTokenSession:
        raise oauth.TikTokOAuthError("OAUTH_CALLBACK_STATE_MISMATCH")

    result = cli.main(
        [cli.EXECUTION_FLAG],
        env={},
        store=store,
        token_transport=SentinelTransport(),
        user_info_transport=FakeUserInfoTransport(_secret("open-id")),
        credential_reader=lambda _env: oauth.TikTokAppCredentials("key", "secret"),
        oauth_authorizer=failed_oauth,
    )
    assert result == 2
    assert _receipt(capsys)["result"] == "OAUTH_CALLBACK_STATE_MISMATCH"
    assert backend.write_calls == 0


def test_existing_credential_fails_before_env_or_oauth_and_never_overwrites(
    capsys: pytest.CaptureFixture[str],
) -> None:
    store, backend = _store()
    existing = secure.CredentialRecord(
        username=_secret("existing-open-id"),
        secret=_secret("existing-refresh"),
    )
    backend.records[TEST_TARGET] = existing
    calls = {"credentials": 0, "oauth": 0}

    def credential_reader(_env: Mapping[str, str] | None) -> oauth.TikTokAppCredentials:
        calls["credentials"] += 1
        raise AssertionError("existing credential must block before env read")

    def authorizer(*_args: Any, **_kwargs: Any) -> oauth.TikTokTokenSession:
        calls["oauth"] += 1
        raise AssertionError("existing credential must block before OAuth")

    result = cli.main(
        [cli.EXECUTION_FLAG],
        env={},
        store=store,
        credential_reader=credential_reader,
        oauth_authorizer=authorizer,
    )
    receipt = _receipt(capsys)
    assert result == 2
    assert receipt["result"] == cli.EXISTING_CREDENTIAL
    assert calls == {"credentials": 0, "oauth": 0}
    assert backend.write_calls == 0
    assert backend.records[TEST_TARGET] == existing


def test_credential_write_failure_is_stable_and_redacted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    backend = FakeCredentialBackend()
    backend.fail_write = True
    store, _ = _store(backend)
    session = _session()
    result = cli.main(
        [cli.EXECUTION_FLAG],
        env={},
        store=store,
        token_transport=SentinelTransport(),
        user_info_transport=FakeUserInfoTransport(session.open_id),
        credential_reader=lambda _env: oauth.TikTokAppCredentials("key", "secret"),
        oauth_authorizer=lambda _credentials, **_kwargs: session,
    )
    receipt = _receipt(capsys)
    assert result == 2
    assert receipt["result"] == "CREDENTIAL_WRITE_FAILED"
    assert receipt["refresh_token_persisted"] is False
    assert backend.write_calls == 1
    assert backend.records == {}


def test_cli_output_and_errors_leak_no_fake_secret_values(
    capsys: pytest.CaptureFixture[str],
) -> None:
    secrets = {
        _secret("client-key-private"),
        _secret("client-secret-private"),
        _secret("access-token-private"),
        _secret("refresh-token-private"),
        _secret("open-id-private"),
    }
    client_key, client_secret, access_token, refresh_token, open_id = tuple(secrets)
    session = _session(
        access_token=access_token,
        refresh_token=refresh_token,
        open_id=open_id,
    )
    store, _backend = _store()
    result = cli.main(
        [cli.EXECUTION_FLAG],
        env={
            oauth.CLIENT_KEY_ENV: client_key,
            oauth.CLIENT_SECRET_ENV: client_secret,
        },
        store=store,
        token_transport=SentinelTransport(),
        user_info_transport=FakeUserInfoTransport(open_id),
        credential_reader=oauth.read_approved_credentials,
        oauth_authorizer=lambda _credentials, **_kwargs: session,
    )
    captured = capsys.readouterr()
    assert result == 0
    assert captured.err == ""
    combined = captured.out + repr(session) + str(session)
    assert not any(secret in combined for secret in secrets)


def test_access_token_never_persists_and_no_content_posting_path_exists(
    capsys: pytest.CaptureFixture[str],
) -> None:
    store, backend = _store()
    session = _session()
    result = cli.main(
        [cli.EXECUTION_FLAG],
        env={},
        store=store,
        token_transport=SentinelTransport(),
        user_info_transport=FakeUserInfoTransport(session.open_id),
        credential_reader=lambda _env: oauth.TikTokAppCredentials("key", "secret"),
        oauth_authorizer=lambda _credentials, **_kwargs: session,
    )
    assert result == 0
    receipt = _receipt(capsys)
    assert receipt["access_token_persisted"] is False
    assert backend.records[TEST_TARGET].secret == session.refresh_token
    assert backend.records[TEST_TARGET].secret != session.access_token

    source = inspect.getsource(cli).casefold()
    forbidden = (
        "video.publish",
        "/v2/post/",
        "video.list(",
        "video.upload(",
        "post_status",
    )
    assert not any(marker in source for marker in forbidden)
