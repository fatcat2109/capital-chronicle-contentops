from __future__ import annotations

import hashlib
import inspect
import io
import json
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Mapping

import pytest

from live_contentops import tiktok_local_desktop_oauth_pkce_v1 as oauth


ROOT = Path(__file__).resolve().parents[1]


def _secret(label: str) -> str:
    return label + "-" + ("Z" * 32)


def _token_payload(
    *,
    scopes: tuple[str, ...] = oauth.REQUIRED_SCOPES,
    access_token: str | None = None,
    refresh_token: str | None = None,
    open_id: str | None = None,
) -> dict[str, Any]:
    return {
        "access_token": access_token or _secret("fake-access-token"),
        "refresh_token": refresh_token or _secret("fake-refresh-token"),
        "open_id": open_id or _secret("fake-open-id"),
        "scope": ",".join(scopes),
        "expires_in": 86400,
        "refresh_expires_in": 31536000,
        "token_type": "Bearer",
    }


class RecordingTransport:
    def __init__(self, payload: Mapping[str, Any]) -> None:
        self.payload = dict(payload)
        self.calls: list[tuple[str, dict[str, str], float]] = []

    def post_form(
        self,
        endpoint: str,
        form: Mapping[str, str],
        *,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        self.calls.append((endpoint, dict(form), timeout_seconds))
        return dict(self.payload)


def _credentials() -> oauth.TikTokAppCredentials:
    return oauth.TikTokAppCredentials(
        client_key=_secret("fake-client-key"),
        client_secret=_secret("fake-client-secret"),
    )


def test_module_import_has_no_runtime_side_effects() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import live_contentops.tiktok_local_desktop_oauth_pkce_v1; print('IMPORTED')",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "IMPORTED"
    assert completed.stderr == ""
    source = inspect.getsource(oauth)
    assert source.count("os.environ") == 1
    assert "if env is None" in source


def test_only_owner_approved_environment_names_are_read() -> None:
    credentials = oauth.read_approved_credentials(
        {
            oauth.CLIENT_KEY_ENV: _secret("approved-key"),
            oauth.CLIENT_SECRET_ENV: _secret("approved-secret"),
            "TIKTOK_CLIENT_KEY": _secret("historical-key"),
            "TIKTOK_CLIENT_SECRET": _secret("historical-secret"),
        }
    )
    assert credentials.client_key == _secret("approved-key")
    assert credentials.client_secret == _secret("approved-secret")
    with pytest.raises(oauth.TikTokOAuthError, match="REQUIRED_CONFIGURATION_ABSENT"):
        oauth.read_approved_credentials(
            {
                "TIKTOK_CLIENT_KEY": _secret("historical-key"),
                "TIKTOK_CLIENT_SECRET": _secret("historical-secret"),
            }
        )


def test_tiktok_desktop_pkce_is_lowercase_hex_sha256() -> None:
    verifier = "A" * 64
    challenge = oauth.derive_tiktok_s256_challenge(verifier)
    assert challenge == hashlib.sha256(verifier.encode("ascii")).hexdigest()
    assert len(challenge) == 64
    assert challenge == challenge.lower()
    assert all(character in "0123456789abcdef" for character in challenge)
    generated = oauth.generate_pkce_verifier()
    assert 43 <= len(generated) <= 128
    assert set(generated).issubset(set(oauth.PKCE_UNRESERVED))


@pytest.mark.parametrize("length", [42, 129])
def test_invalid_pkce_verifier_length_is_rejected(length: int) -> None:
    with pytest.raises(oauth.TikTokOAuthError, match="PKCE_VERIFIER_LENGTH_INVALID"):
        oauth.generate_pkce_verifier(length)


def test_authorization_request_is_exact_and_never_requests_direct_post() -> None:
    state = _secret("fake-state")
    verifier = "B" * 64
    context = oauth.build_authorization_context(
        _secret("fake-client-key"),
        state=state,
        code_verifier=verifier,
    )
    parsed = urllib.parse.urlsplit(context.authorization_url)
    query = urllib.parse.parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "www.tiktok.com"
    assert parsed.path == "/v2/auth/authorize/"
    assert query["redirect_uri"] == [oauth.CALLBACK_URI]
    assert query["scope"] == [",".join(oauth.REQUIRED_SCOPES)]
    assert query["response_type"] == ["code"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["code_challenge"] == [hashlib.sha256(verifier.encode()).hexdigest()]
    assert "video.publish" not in query["scope"][0]
    assert "client_secret" not in query
    assert repr(context) == "AuthorizationContext(REDACTED_TRANSIENT_MATERIAL)"


@pytest.mark.parametrize(
    ("target", "classification"),
    [
        (f"{oauth.CALLBACK_PATH}?code=x&state=wrong", "OAUTH_CALLBACK_STATE_MISMATCH"),
        (f"{oauth.CALLBACK_PATH}?code=x", "OAUTH_CALLBACK_STATE_MISSING"),
        (f"{oauth.CALLBACK_PATH}?state=expected", "OAUTH_CALLBACK_CODE_MISSING"),
        (
            f"{oauth.CALLBACK_PATH}?error=access_denied&error_description=sensitive&state=expected",
            "OAUTH_PROVIDER_ERROR",
        ),
        ("/wrong/path?code=x&state=expected", "OAUTH_CALLBACK_WRONG_PATH"),
        (
            f"{oauth.CALLBACK_PATH}?code=one&code=two&state=expected",
            "OAUTH_CALLBACK_MALFORMED_QUERY",
        ),
        (f"{oauth.CALLBACK_PATH}?unknown=x&state=expected", "OAUTH_CALLBACK_MALFORMED_QUERY"),
    ],
)
def test_adversarial_callbacks_fail_closed(target: str, classification: str) -> None:
    with pytest.raises(oauth.TikTokOAuthError) as captured:
        oauth.parse_callback_target(target, expected_state="expected")
    assert str(captured.value) == classification
    assert "sensitive" not in str(captured.value)


def test_valid_callback_uses_safe_result_string() -> None:
    authorization = oauth.parse_callback_target(
        f"{oauth.CALLBACK_PATH}?code={urllib.parse.quote(_secret('fake-code'))}&state=expected",
        expected_state="expected",
    )
    assert repr(authorization) == "CallbackAuthorization(REDACTED_AUTHORIZATION_CODE)"
    assert _secret("fake-code") not in str(authorization)


def test_listener_timeout_is_bounded_and_browser_url_is_not_printed(capsys: Any) -> None:
    context = oauth.build_authorization_context(_secret("fake-client-key"))
    with pytest.raises(oauth.TikTokOAuthError, match="OAUTH_CALLBACK_TIMEOUT"):
        oauth.receive_authorization_code(
            context,
            browser_opener=lambda _url: True,
            timeout_seconds=0.05,
        )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_browser_open_failure_stops_before_any_token_exchange() -> None:
    context = oauth.build_authorization_context(_secret("fake-client-key"))
    with pytest.raises(oauth.TikTokOAuthError, match="OAUTH_BROWSER_LAUNCH_FAILED"):
        oauth.receive_authorization_code(
            context,
            browser_opener=lambda _url: False,
            timeout_seconds=0.25,
        )


def test_authorization_code_exchange_shape_and_single_attempt() -> None:
    transport = RecordingTransport(_token_payload())
    session = oauth.exchange_authorization_code(
        _credentials(),
        oauth.CallbackAuthorization(_secret("fake-code")),
        code_verifier="C" * 64,
        transport=transport,
        timeout_seconds=7.0,
    )
    assert len(transport.calls) == 1
    endpoint, form, timeout = transport.calls[0]
    assert endpoint == oauth.TOKEN_ENDPOINT
    assert set(form) == {
        "client_key",
        "client_secret",
        "code",
        "grant_type",
        "redirect_uri",
        "code_verifier",
    }
    assert form["grant_type"] == "authorization_code"
    assert form["redirect_uri"] == oauth.CALLBACK_URI
    assert timeout == 7.0
    assert session.required_scopes_satisfied is True


@pytest.mark.parametrize(
    ("missing_key", "classification"),
    [
        ("access_token", "TOKEN_RESPONSE_ACCESS_TOKEN_MISSING"),
        ("refresh_token", "TOKEN_RESPONSE_REFRESH_TOKEN_MISSING"),
        ("open_id", "TOKEN_RESPONSE_OPEN_ID_MISSING"),
    ],
)
def test_required_token_fields_are_enforced(missing_key: str, classification: str) -> None:
    payload = _token_payload()
    payload.pop(missing_key)
    transport = RecordingTransport(payload)
    with pytest.raises(oauth.TikTokOAuthError) as captured:
        oauth.exchange_authorization_code(
            _credentials(),
            oauth.CallbackAuthorization(_secret("fake-code")),
            code_verifier="D" * 64,
            transport=transport,
        )
    assert str(captured.value) == classification


def test_scope_subset_is_truthfully_incomplete_and_extra_scopes_are_allowed() -> None:
    incomplete = RecordingTransport(
        _token_payload(scopes=("user.info.basic", "video.list"))
    )
    session = oauth.exchange_authorization_code(
        _credentials(),
        oauth.CallbackAuthorization(_secret("fake-code")),
        code_verifier="E" * 64,
        transport=incomplete,
    )
    assert session.required_scopes_satisfied is False
    assert session.result == "TOKEN_RECEIVED_REQUIRED_SCOPES_INCOMPLETE"

    extra = RecordingTransport(
        _token_payload(scopes=oauth.REQUIRED_SCOPES + ("user.info.profile",))
    )
    session = oauth.exchange_authorization_code(
        _credentials(),
        oauth.CallbackAuthorization(_secret("fake-code")),
        code_verifier="F" * 64,
        transport=extra,
    )
    assert session.required_scopes_satisfied is True
    assert "user.info.profile" in session.granted_scopes


def test_refresh_exchange_honors_rotated_refresh_token() -> None:
    old_refresh = _secret("old-refresh-token")
    new_refresh = _secret("new-refresh-token")
    transport = RecordingTransport(_token_payload(refresh_token=new_refresh))
    session = oauth.refresh_token_session(
        _credentials(),
        old_refresh,
        transport=transport,
    )
    assert len(transport.calls) == 1
    endpoint, form, _timeout = transport.calls[0]
    assert endpoint == oauth.TOKEN_ENDPOINT
    assert set(form) == {
        "client_key",
        "client_secret",
        "grant_type",
        "refresh_token",
    }
    assert form["grant_type"] == "refresh_token"
    assert form["refresh_token"] == old_refresh
    assert session.refresh_token == new_refresh
    assert old_refresh != session.refresh_token


class _FakeResponse:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self._body = body
        self.status = status

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def read(self) -> bytes:
        return self._body

    def getcode(self) -> int:
        return self.status


def test_real_transport_reduces_http_and_json_errors_to_safe_classifications() -> None:
    def http_error(_request: Any, *, timeout: float) -> Any:
        raise urllib.error.HTTPError(oauth.TOKEN_ENDPOINT, 400, "bad", {}, None)

    transport = oauth.UrllibFormTokenTransport(opener=http_error)
    with pytest.raises(oauth.TikTokOAuthError, match="TOKEN_HTTP_ERROR"):
        transport.post_form(oauth.TOKEN_ENDPOINT, {"secret": _secret("fake")}, timeout_seconds=1)

    transport = oauth.UrllibFormTokenTransport(
        opener=lambda _request, timeout: _FakeResponse(b"not-json")
    )
    with pytest.raises(oauth.TikTokOAuthError, match="TOKEN_RESPONSE_MALFORMED_JSON"):
        transport.post_form(oauth.TOKEN_ENDPOINT, {"secret": _secret("fake")}, timeout_seconds=1)


def test_token_and_credential_string_forms_and_receipt_are_redacted() -> None:
    secrets_to_find = {
        _secret("fake-client-key"),
        _secret("fake-client-secret"),
        _secret("fake-access-token"),
        _secret("fake-refresh-token"),
        _secret("fake-open-id"),
    }
    credentials = _credentials()
    session = oauth.exchange_authorization_code(
        credentials,
        oauth.CallbackAuthorization(_secret("fake-code")),
        code_verifier="G" * 64,
        transport=RecordingTransport(_token_payload()),
    )
    output = json.dumps(session.redacted_receipt(), sort_keys=True)
    combined = output + repr(session) + str(session) + repr(credentials) + str(credentials)
    assert not any(secret in combined for secret in secrets_to_find)
    assert session.redacted_receipt()["secrets_persisted"] is False
    assert session.redacted_receipt()["environment_mutated"] is False


def test_local_fake_e2e_and_refresh_leak_nothing_or_persist_anything(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials = _credentials()
    authorization_code = _secret("fake-authorization-code")
    access_token = _secret("fake-access-token")
    refresh_token = _secret("fake-refresh-token")
    open_id = _secret("fake-open-id")
    rotated_refresh = _secret("fake-rotated-refresh-token")
    secret_values = {
        credentials.client_key,
        credentials.client_secret,
        authorization_code,
        access_token,
        refresh_token,
        open_id,
        rotated_refresh,
    }
    controlled_env = {
        oauth.CLIENT_KEY_ENV: credentials.client_key,
        oauth.CLIENT_SECRET_ENV: credentials.client_secret,
    }
    controlled_env_before = dict(controlled_env)
    assert oauth.read_approved_credentials(controlled_env) == credentials
    monkeypatch.chdir(tmp_path)
    callback_errors: list[str] = []
    callback_threads: list[threading.Thread] = []

    def browser_opener(authorization_url: str) -> bool:
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(authorization_url).query)
        state = query["state"][0]

        def send_callback() -> None:
            callback_url = oauth.CALLBACK_URI + "?" + urllib.parse.urlencode(
                {"code": authorization_code, "state": state}
            )
            try:
                with urllib.request.urlopen(callback_url, timeout=2.0) as response:
                    response.read()
            except Exception as exc:  # pragma: no cover - assertion reports only class name
                callback_errors.append(type(exc).__name__)

        thread = threading.Thread(target=send_callback, daemon=True)
        callback_threads.append(thread)
        thread.start()
        return True

    transport = RecordingTransport(
        _token_payload(
            access_token=access_token,
            refresh_token=refresh_token,
            open_id=open_id,
        )
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        session = oauth.authorize_interactively(
            credentials,
            transport=transport,
            browser_opener=browser_opener,
            callback_timeout_seconds=2.0,
        )
        refresh_transport = RecordingTransport(
            _token_payload(
                access_token=_secret("fake-refreshed-access-token"),
                refresh_token=rotated_refresh,
                open_id=open_id,
            )
        )
        refreshed = oauth.refresh_token_session(
            credentials,
            session.refresh_token,
            transport=refresh_transport,
        )
        receipt_text = json.dumps(session.redacted_receipt(), sort_keys=True)
        refresh_receipt_text = json.dumps(refreshed.redacted_receipt(), sort_keys=True)
    for thread in callback_threads:
        thread.join(timeout=2.0)
    combined = "\n".join(
        [
            stdout.getvalue(),
            stderr.getvalue(),
            receipt_text,
            refresh_receipt_text,
            repr(session),
            str(session),
            repr(refreshed),
            str(refreshed),
        ]
    )
    assert callback_errors == []
    assert session.required_scopes_satisfied is True
    assert refreshed.refresh_token == rotated_refresh
    assert not any(secret in combined for secret in secret_values)
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""
    assert list(tmp_path.iterdir()) == []
    assert controlled_env == controlled_env_before
    with pytest.raises((OSError, urllib.error.URLError)):
        urllib.request.urlopen(
            oauth.CALLBACK_URI + "?code=late&state=late",
            timeout=0.25,
        )


def test_cli_requires_explicit_confirmation_without_reading_environment() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/run_tiktok_local_desktop_oauth_pkce_v1.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(completed.stdout)
    assert completed.returncode == 2
    assert completed.stderr == ""
    assert receipt == {
        "environment_mutated": False,
        "public_writes": 0,
        "result": "EXPLICIT_SUPERVISED_OAUTH_CONFIRMATION_REQUIRED",
        "secrets_persisted": False,
    }


def test_source_contains_no_persistence_environment_mutation_or_content_posting_execution() -> None:
    source = inspect.getsource(oauth).casefold()
    forbidden = (
        "setx",
        "winreg",
        "keyring",
        "sqlite",
        "dotenv",
        "write_text",
        "write_bytes",
        "post/publish",
        "video.publish",
    )
    assert not any(marker in source for marker in forbidden)
    assert "os.environ[" not in source
    assert "os.environ.update" not in source
    assert set(oauth.REQUIRED_SCOPES) == {
        "user.info.basic",
        "video.list",
        "video.upload",
    }
