"""Supervised TikTok Desktop OAuth PKCE bootstrap with zero token persistence.

The module is deliberately TikTok-specific. Importing it performs no environment read,
listener bind, browser launch, or network request. The real supervised entrypoint is the
only caller that may read the two approved application-credential environment variables.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import string
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event
from typing import Any, Callable, Mapping, Protocol


CLIENT_KEY_ENV = "CONTENTOPS_TIKTOK_CLIENT_KEY"
CLIENT_SECRET_ENV = "CONTENTOPS_TIKTOK_CLIENT_SECRET"

CALLBACK_HOST = "127.0.0.1"
CALLBACK_PORT = 8765
CALLBACK_PATH = "/oauth/tiktok/callback"
CALLBACK_URI = f"http://{CALLBACK_HOST}:{CALLBACK_PORT}{CALLBACK_PATH}"

AUTHORIZATION_ENDPOINT = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_ENDPOINT = "https://open.tiktokapis.com/v2/oauth/token/"
REQUIRED_SCOPES = ("user.info.basic", "video.list", "video.upload")

PKCE_UNRESERVED = string.ascii_letters + string.digits + "-._~"
DEFAULT_PKCE_VERIFIER_LENGTH = 64
DEFAULT_CALLBACK_TIMEOUT_SECONDS = 300.0
DEFAULT_HTTP_TIMEOUT_SECONDS = 15.0


class TikTokOAuthError(RuntimeError):
    """A nonsecret, stable OAuth failure classification."""

    def __init__(self, classification: str) -> None:
        super().__init__(classification)
        self.classification = classification


@dataclass(frozen=True, repr=False)
class TikTokAppCredentials:
    """Application credentials whose string forms never expose their values."""

    client_key: str
    client_secret: str

    def __post_init__(self) -> None:
        if not self.client_key.strip() or not self.client_secret.strip():
            raise TikTokOAuthError("REQUIRED_CONFIGURATION_ABSENT")

    def __repr__(self) -> str:
        return "TikTokAppCredentials(REDACTED)"

    __str__ = __repr__


@dataclass(frozen=True, repr=False)
class AuthorizationContext:
    """Transient state for exactly one authorization attempt."""

    state: str
    code_verifier: str
    code_challenge: str
    authorization_url: str

    def __repr__(self) -> str:
        return "AuthorizationContext(REDACTED_TRANSIENT_MATERIAL)"

    __str__ = __repr__


@dataclass(frozen=True, repr=False)
class CallbackAuthorization:
    """Validated single-use authorization code held only in memory."""

    code: str

    def __repr__(self) -> str:
        return "CallbackAuthorization(REDACTED_AUTHORIZATION_CODE)"

    __str__ = __repr__


@dataclass(frozen=True, repr=False)
class TikTokTokenSession:
    """In-memory token result; repr/str and receipts are secret-free."""

    access_token: str
    refresh_token: str
    open_id: str
    granted_scopes: tuple[str, ...]
    expires_in: int
    refresh_expires_in: int
    token_type: str

    def __post_init__(self) -> None:
        if not self.access_token or not self.refresh_token or not self.open_id:
            raise TikTokOAuthError("TOKEN_SESSION_SECRET_MATERIAL_MISSING")

    def __repr__(self) -> str:
        return "TikTokTokenSession(REDACTED_IN_MEMORY_ONLY)"

    __str__ = __repr__

    @property
    def required_scopes_satisfied(self) -> bool:
        return set(REQUIRED_SCOPES).issubset(self.granted_scopes)

    @property
    def result(self) -> str:
        if self.required_scopes_satisfied:
            return "TOKEN_RECEIVED_REQUIRED_SCOPES_SATISFIED"
        return "TOKEN_RECEIVED_REQUIRED_SCOPES_INCOMPLETE"

    def redacted_receipt(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "callback_uri": CALLBACK_URI,
            "requested_scopes": list(REQUIRED_SCOPES),
            "granted_scopes": list(self.granted_scopes),
            "state_validated": True,
            "access_token_received": True,
            "refresh_token_received": True,
            "open_id_received": True,
            "required_scopes_satisfied": self.required_scopes_satisfied,
            "refresh_capable": True,
            "secrets_persisted": False,
            "environment_mutated": False,
            "content_posting_calls": 0,
            "media_uploads": 0,
            "public_writes": 0,
        }


class FormTokenTransport(Protocol):
    """Injected seam for the single token POST; tests provide a fake."""

    def post_form(
        self,
        endpoint: str,
        form: Mapping[str, str],
        *,
        timeout_seconds: float,
    ) -> Mapping[str, Any]: ...


class UrllibFormTokenTransport:
    """Bounded one-attempt form transport for a future supervised run."""

    def __init__(
        self,
        *,
        opener: Callable[..., Any] = urllib.request.urlopen,
    ) -> None:
        self._opener = opener

    def post_form(
        self,
        endpoint: str,
        form: Mapping[str, str],
        *,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        request = urllib.request.Request(
            endpoint,
            data=urllib.parse.urlencode(dict(form)).encode("ascii"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cache-Control": "no-cache",
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=timeout_seconds) as response:
                status = int(getattr(response, "status", response.getcode()))
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise TikTokOAuthError("TOKEN_HTTP_ERROR") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise TikTokOAuthError("TOKEN_TRANSPORT_UNAVAILABLE") from None
        if status != 200:
            raise TikTokOAuthError("TOKEN_HTTP_ERROR")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise TikTokOAuthError("TOKEN_RESPONSE_MALFORMED_JSON") from None
        if not isinstance(payload, dict):
            raise TikTokOAuthError("TOKEN_RESPONSE_MALFORMED_JSON")
        return payload


def read_approved_credentials(
    env: Mapping[str, str] | None = None,
) -> TikTokAppCredentials:
    """Read only the two owner-approved names when explicitly called."""

    source = os.environ if env is None else env
    return TikTokAppCredentials(
        client_key=str(source.get(CLIENT_KEY_ENV) or ""),
        client_secret=str(source.get(CLIENT_SECRET_ENV) or ""),
    )


def generate_state() -> str:
    """Create fresh CSPRNG anti-forgery state without persistence."""

    return secrets.token_urlsafe(32)


def generate_pkce_verifier(length: int = DEFAULT_PKCE_VERIFIER_LENGTH) -> str:
    """Create a TikTok Desktop verifier from OAuth unreserved characters."""

    if not 43 <= length <= 128:
        raise TikTokOAuthError("PKCE_VERIFIER_LENGTH_INVALID")
    return "".join(secrets.choice(PKCE_UNRESERVED) for _ in range(length))


def derive_tiktok_s256_challenge(code_verifier: str) -> str:
    """Apply TikTok Desktop's documented lowercase hex SHA-256 convention."""

    if not 43 <= len(code_verifier) <= 128 or any(
        character not in PKCE_UNRESERVED for character in code_verifier
    ):
        raise TikTokOAuthError("PKCE_VERIFIER_INVALID")
    return hashlib.sha256(code_verifier.encode("ascii")).hexdigest()


def build_authorization_context(
    client_key: str,
    *,
    state: str | None = None,
    code_verifier: str | None = None,
) -> AuthorizationContext:
    """Build but never print the exact current TikTok Desktop request."""

    if not client_key.strip():
        raise TikTokOAuthError("CLIENT_KEY_ABSENT")
    current_state = state or generate_state()
    verifier = code_verifier or generate_pkce_verifier()
    challenge = derive_tiktok_s256_challenge(verifier)
    query = urllib.parse.urlencode(
        {
            "client_key": client_key,
            "response_type": "code",
            "scope": ",".join(REQUIRED_SCOPES),
            "redirect_uri": CALLBACK_URI,
            "state": current_state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return AuthorizationContext(
        state=current_state,
        code_verifier=verifier,
        code_challenge=challenge,
        authorization_url=AUTHORIZATION_ENDPOINT + "?" + query,
    )


def _parse_query_exactly(query: str) -> dict[str, str]:
    try:
        pairs = urllib.parse.parse_qsl(
            query,
            keep_blank_values=True,
            strict_parsing=True,
            max_num_fields=10,
        )
    except ValueError:
        raise TikTokOAuthError("OAUTH_CALLBACK_MALFORMED_QUERY") from None
    allowed = {"code", "scopes", "state", "error", "error_description"}
    result: dict[str, str] = {}
    for key, value in pairs:
        if key not in allowed or key in result:
            raise TikTokOAuthError("OAUTH_CALLBACK_MALFORMED_QUERY")
        result[key] = value
    return result


def parse_callback_target(
    target: str,
    *,
    expected_state: str,
) -> CallbackAuthorization:
    """Validate path, query shape, state, provider error, and code exactly."""

    parsed = urllib.parse.urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        raise TikTokOAuthError("OAUTH_CALLBACK_MALFORMED_QUERY")
    if parsed.path != CALLBACK_PATH:
        raise TikTokOAuthError("OAUTH_CALLBACK_WRONG_PATH")
    values = _parse_query_exactly(parsed.query)
    received_state = values.get("state", "")
    if not received_state:
        raise TikTokOAuthError("OAUTH_CALLBACK_STATE_MISSING")
    if not hmac.compare_digest(received_state, expected_state):
        raise TikTokOAuthError("OAUTH_CALLBACK_STATE_MISMATCH")
    if values.get("error"):
        raise TikTokOAuthError("OAUTH_PROVIDER_ERROR")
    code = values.get("code", "")
    if not code:
        raise TikTokOAuthError("OAUTH_CALLBACK_CODE_MISSING")
    return CallbackAuthorization(code=code)


def _callback_handler(expected_state: str) -> type[BaseHTTPRequestHandler]:
    class BoundedTikTokCallbackHandler(BaseHTTPRequestHandler):
        completed = Event()
        result: CallbackAuthorization | None = None
        error: TikTokOAuthError | None = None

        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def do_GET(self) -> None:  # noqa: N802
            try:
                type(self).result = parse_callback_target(
                    self.path,
                    expected_state=expected_state,
                )
            except TikTokOAuthError as exc:
                type(self).error = exc
                status = 404 if exc.classification == "OAUTH_CALLBACK_WRONG_PATH" else 400
                body = b"TikTok authorization was not accepted. You may close this tab."
            else:
                status = 200
                body = b"TikTok authorization was received securely. You may close this tab."
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
            type(self).completed.set()

    return BoundedTikTokCallbackHandler


class _OneShotLoopbackServer(HTTPServer):
    allow_reuse_address = True


def receive_authorization_code(
    context: AuthorizationContext,
    *,
    browser_opener: Callable[[str], Any] = webbrowser.open,
    timeout_seconds: float = DEFAULT_CALLBACK_TIMEOUT_SECONDS,
) -> CallbackAuthorization:
    """Run one bounded listener and stop after the first callback or timeout."""

    if timeout_seconds <= 0:
        raise TikTokOAuthError("OAUTH_CALLBACK_TIMEOUT")
    handler = _callback_handler(context.state)
    try:
        server = _OneShotLoopbackServer((CALLBACK_HOST, CALLBACK_PORT), handler)
    except OSError:
        raise TikTokOAuthError("OAUTH_CALLBACK_LISTENER_UNAVAILABLE") from None
    server.timeout = min(0.25, timeout_seconds)
    try:
        try:
            opened = browser_opener(context.authorization_url)
        except Exception:
            raise TikTokOAuthError("OAUTH_BROWSER_LAUNCH_FAILED") from None
        if opened is False:
            raise TikTokOAuthError("OAUTH_BROWSER_LAUNCH_FAILED")
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline and not handler.completed.is_set():
            server.handle_request()
    finally:
        server.server_close()
    if not handler.completed.is_set():
        raise TikTokOAuthError("OAUTH_CALLBACK_TIMEOUT")
    if handler.error is not None:
        raise TikTokOAuthError(handler.error.classification)
    if handler.result is None:
        raise TikTokOAuthError("OAUTH_CALLBACK_CODE_MISSING")
    return handler.result


def _positive_int(payload: Mapping[str, Any], key: str) -> int:
    try:
        value = int(payload.get(key))
    except (TypeError, ValueError):
        raise TikTokOAuthError("TOKEN_RESPONSE_EXPIRY_INVALID") from None
    if value <= 0:
        raise TikTokOAuthError("TOKEN_RESPONSE_EXPIRY_INVALID")
    return value


def _session_from_token_payload(payload: Mapping[str, Any]) -> TikTokTokenSession:
    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    open_id = payload.get("open_id")
    scope = payload.get("scope")
    if not isinstance(access_token, str) or not access_token:
        raise TikTokOAuthError("TOKEN_RESPONSE_ACCESS_TOKEN_MISSING")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise TikTokOAuthError("TOKEN_RESPONSE_REFRESH_TOKEN_MISSING")
    if not isinstance(open_id, str) or not open_id:
        raise TikTokOAuthError("TOKEN_RESPONSE_OPEN_ID_MISSING")
    if not isinstance(scope, str) or not scope.strip():
        raise TikTokOAuthError("TOKEN_RESPONSE_SCOPES_MISSING")
    granted_scopes = tuple(sorted(set(scope.replace(",", " ").split())))
    return TikTokTokenSession(
        access_token=access_token,
        refresh_token=refresh_token,
        open_id=open_id,
        granted_scopes=granted_scopes,
        expires_in=_positive_int(payload, "expires_in"),
        refresh_expires_in=_positive_int(payload, "refresh_expires_in"),
        token_type=str(payload.get("token_type") or "Bearer"),
    )


def exchange_authorization_code(
    credentials: TikTokAppCredentials,
    authorization: CallbackAuthorization,
    *,
    code_verifier: str,
    transport: FormTokenTransport,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> TikTokTokenSession:
    """Exchange one single-use code once; no retries and no persistence."""

    payload = transport.post_form(
        TOKEN_ENDPOINT,
        {
            "client_key": credentials.client_key,
            "client_secret": credentials.client_secret,
            "code": authorization.code,
            "grant_type": "authorization_code",
            "redirect_uri": CALLBACK_URI,
            "code_verifier": code_verifier,
        },
        timeout_seconds=timeout_seconds,
    )
    return _session_from_token_payload(payload)


def refresh_token_session(
    credentials: TikTokAppCredentials,
    refresh_token: str,
    *,
    transport: FormTokenTransport,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> TikTokTokenSession:
    """Exchange a transient refresh token and honor provider token rotation."""

    if not refresh_token:
        raise TikTokOAuthError("REFRESH_TOKEN_ABSENT")
    payload = transport.post_form(
        TOKEN_ENDPOINT,
        {
            "client_key": credentials.client_key,
            "client_secret": credentials.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout_seconds=timeout_seconds,
    )
    return _session_from_token_payload(payload)


def authorize_interactively(
    credentials: TikTokAppCredentials,
    *,
    transport: FormTokenTransport,
    browser_opener: Callable[[str], Any] = webbrowser.open,
    callback_timeout_seconds: float = DEFAULT_CALLBACK_TIMEOUT_SECONDS,
    http_timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> TikTokTokenSession:
    """Complete supervised consent and return tokens only to the in-memory caller."""

    context = build_authorization_context(credentials.client_key)
    authorization = receive_authorization_code(
        context,
        browser_opener=browser_opener,
        timeout_seconds=callback_timeout_seconds,
    )
    return exchange_authorization_code(
        credentials,
        authorization,
        code_verifier=context.code_verifier,
        transport=transport,
        timeout_seconds=http_timeout_seconds,
    )


def failure_receipt(error: TikTokOAuthError) -> dict[str, Any]:
    """Create a stable receipt without echoing provider or secret material."""

    return {
        "result": error.classification,
        "callback_uri": CALLBACK_URI,
        "requested_scopes": list(REQUIRED_SCOPES),
        "granted_scopes": [],
        "state_validated": False,
        "access_token_received": False,
        "refresh_token_received": False,
        "open_id_received": False,
        "required_scopes_satisfied": False,
        "refresh_capable": False,
        "secrets_persisted": False,
        "environment_mutated": False,
        "content_posting_calls": 0,
        "media_uploads": 0,
        "public_writes": 0,
    }
