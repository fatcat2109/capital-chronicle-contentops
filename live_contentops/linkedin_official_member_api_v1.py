"""Official LinkedIn personal-member OAuth, secret storage, transport, and readback.

This is the only autonomous LinkedIn publication boundary.  It never imports or invokes the
historical Edge/CDP adapter.  OAuth is operator-driven, credentials are protected with Windows
DPAPI for the current user, and all provider errors are reduced to nonsecret classifications.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import secrets
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from ctypes import wintypes
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Event
from typing import Any, Callable, Mapping, Optional


TRANSPORT_VERSION = "contentops.linkedin_official_member_api_transport.v1"
AUTH_METADATA_VERSION = "contentops.linkedin_official_member_api_auth_metadata.v1"
TOKEN_STORE_BINDING = "WINDOWS_DPAPI_CURRENT_USER:contentops.linkedin.member.v1"
CALLBACK_HOST = "127.0.0.1"
CALLBACK_PORT = 8765
CALLBACK_PATH = "/linkedin/oauth/callback"
CALLBACK_URI = f"http://{CALLBACK_HOST}:{CALLBACK_PORT}{CALLBACK_PATH}"
AUTHORIZATION_ENDPOINT = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_ENDPOINT = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_ENDPOINT = "https://api.linkedin.com/v2/userinfo"
UGC_POSTS_ENDPOINT = "https://api.linkedin.com/v2/ugcPosts"
POSTS_READBACK_ENDPOINT = "https://api.linkedin.com/rest/posts"
LINKEDIN_READBACK_VERSION = "202605"
REQUIRED_SCOPES = ("openid", "profile", "w_member_social")
READ_SCOPE = "r_member_social"
DEFAULT_AUTH_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\linkedin_official_member_api")
EXPIRING_WITHIN_DAYS = 7


class LinkedInOfficialApiError(RuntimeError):
    """A safe, nonsecret LinkedIn boundary failure."""

    def __init__(self, classification: str, *, http_status: int | None = None) -> None:
        super().__init__(classification)
        self.classification = classification
        self.http_status = http_status


class LinkedInAmbiguousWriteError(LinkedInOfficialApiError):
    """The request crossed the provider boundary without an authoritative response."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def env_name_presence(env: Mapping[str, str] | None = None) -> dict[str, bool]:
    source = os.environ if env is None else env
    return {
        name: bool(str(source.get(name) or ""))
        for name in ("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_OAUTH_REDIRECT_URI")
    }


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _dpapi_transform(data: bytes, *, protect: bool) -> bytes:
    if os.name != "nt":
        raise LinkedInOfficialApiError("WINDOWS_DPAPI_UNAVAILABLE")
    buffer = ctypes.create_string_buffer(data)
    incoming = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    outgoing = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    function = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    ok = function(
        ctypes.byref(incoming), None, None, None, None, 0,
        ctypes.byref(outgoing),
    )
    if not ok:
        raise LinkedInOfficialApiError("WINDOWS_DPAPI_OPERATION_FAILED")
    try:
        return ctypes.string_at(outgoing.pbData, outgoing.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(outgoing.pbData)


class WindowsDpapiTokenStore:
    """Current-user DPAPI store; the on-disk bytes are never plaintext credentials."""

    def __init__(
        self,
        auth_root: str | Path = DEFAULT_AUTH_ROOT,
        *,
        protect: Callable[[bytes], bytes] | None = None,
        unprotect: Callable[[bytes], bytes] | None = None,
    ) -> None:
        self.auth_root = Path(auth_root)
        self.secret_path = self.auth_root / "linkedin_member_credentials.dpapi"
        self.metadata_path = self.auth_root / "auth_metadata_v1.json"
        self._protect = protect or (lambda value: _dpapi_transform(value, protect=True))
        self._unprotect = unprotect or (lambda value: _dpapi_transform(value, protect=False))

    def write(self, credentials: Mapping[str, Any], metadata: Mapping[str, Any]) -> None:
        secret_payload = json.dumps(dict(credentials), sort_keys=True, separators=(",", ":")).encode("utf-8")
        _atomic_write(self.secret_path, self._protect(secret_payload))
        _atomic_write(
            self.metadata_path,
            (json.dumps(dict(metadata), indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )

    def read_credentials(self) -> dict[str, Any]:
        try:
            decrypted = self._unprotect(self.secret_path.read_bytes())
            result = json.loads(decrypted.decode("utf-8"))
        except FileNotFoundError as exc:
            raise LinkedInOfficialApiError("AUTH_UNAVAILABLE") from exc
        except LinkedInOfficialApiError:
            raise
        except Exception as exc:
            raise LinkedInOfficialApiError("SECURE_TOKEN_STORE_UNREADABLE") from exc
        if not isinstance(result, dict) or not str(result.get("access_token") or ""):
            raise LinkedInOfficialApiError("SECURE_TOKEN_STORE_INVALID")
        return result

    def read_metadata(self) -> dict[str, Any]:
        try:
            result = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except Exception as exc:
            raise LinkedInOfficialApiError("AUTH_METADATA_UNREADABLE") from exc
        return dict(result) if isinstance(result, dict) else {}


def _request_json(
    request: urllib.request.Request,
    *,
    timeout_seconds: float,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> tuple[int, dict[str, Any], Mapping[str, str]]:
    try:
        with opener(request, timeout=timeout_seconds) as response:
            status = int(getattr(response, "status", response.getcode()))
            raw = response.read()
            headers = response.headers
    except urllib.error.HTTPError as exc:
        raise LinkedInOfficialApiError(
            "AUTH_EXPIRED_OR_REAUTH_REQUIRED" if exc.code == 401 else
            "PERMISSION_MISSING" if exc.code == 403 else
            "PROVIDER_REQUEST_REJECTED",
            http_status=int(exc.code),
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LinkedInOfficialApiError("TRANSPORT_UNAVAILABLE") from exc
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LinkedInOfficialApiError("PROVIDER_RESPONSE_INVALID", http_status=status) from exc
    return status, dict(payload) if isinstance(payload, dict) else {}, headers


def build_authorization_url(*, client_id: str, state: str, redirect_uri: str = CALLBACK_URI) -> str:
    query = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": " ".join(REQUIRED_SCOPES),
    })
    return AUTHORIZATION_ENDPOINT + "?" + query


def exchange_authorization_code(
    *,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    timeout_seconds: float = 15.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }).encode("ascii")
    request = urllib.request.Request(
        TOKEN_ENDPOINT, data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    status, payload, _ = _request_json(request, timeout_seconds=timeout_seconds, opener=opener)
    if status != 200 or not str(payload.get("access_token") or ""):
        raise LinkedInOfficialApiError("TOKEN_EXCHANGE_FAILED", http_status=status)
    return payload


def resolve_member_identity(
    access_token: str,
    *,
    timeout_seconds: float = 15.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, str]:
    request = urllib.request.Request(
        USERINFO_ENDPOINT,
        headers={"Authorization": "Bearer " + access_token},
        method="GET",
    )
    status, payload, _ = _request_json(request, timeout_seconds=timeout_seconds, opener=opener)
    subject = str(payload.get("sub") or "").strip()
    display_name = " ".join(str(payload.get("name") or "").split())
    if status != 200 or not subject or not display_name:
        raise LinkedInOfficialApiError("MEMBER_IDENTITY_UNAVAILABLE", http_status=status)
    if display_name.casefold() != "jim pham":
        raise LinkedInOfficialApiError("IDENTITY_MISMATCH")
    return {
        "subject": subject,
        "person_urn": "urn:li:person:" + subject,
        "display_name": display_name,
    }


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    expected_state = ""
    result: dict[str, str] = {}
    completed = Event()

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return
        values = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        state = (values.get("state") or [""])[0]
        if not state or not secrets.compare_digest(state, self.expected_state):
            type(self).result = {"error": "OAUTH_STATE_MISMATCH"}
            self.send_response(401)
            body = b"LinkedIn authorization rejected: state mismatch. You may close this tab."
        elif values.get("error"):
            provider_error = (values.get("error") or [""])[0].casefold()
            classification = (
                "OAUTH_SCOPE_PRODUCT_ACCESS_UNAVAILABLE"
                if "scope" in provider_error
                else "OAUTH_OPERATOR_DENIED_OR_PROVIDER_ERROR"
            )
            type(self).result = {"error": classification}
            self.send_response(400)
            body = b"LinkedIn authorization was not completed. You may close this tab."
        elif not (values.get("code") or [""])[0]:
            type(self).result = {"error": "OAUTH_CODE_MISSING"}
            self.send_response(400)
            body = b"LinkedIn authorization code was missing. You may close this tab."
        else:
            type(self).result = {"code": (values.get("code") or [""])[0]}
            self.send_response(200)
            body = b"LinkedIn authorization received securely. You may close this tab."
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        type(self).completed.set()


def authorize_interactively(
    *,
    env: Mapping[str, str] | None = None,
    auth_root: str | Path = DEFAULT_AUTH_ROOT,
    timeout_seconds: float = 300.0,
    open_browser: bool = True,
    opener: Callable[..., Any] = urllib.request.urlopen,
    browser_opener: Callable[[str], Any] = webbrowser.open,
    token_store: WindowsDpapiTokenStore | None = None,
) -> dict[str, Any]:
    source = os.environ if env is None else env
    presence = env_name_presence(source)
    if not all(presence.values()):
        raise LinkedInOfficialApiError("REQUIRED_CONFIGURATION_ABSENT")
    redirect_uri = str(source.get("LINKEDIN_OAUTH_REDIRECT_URI") or "")
    if redirect_uri != CALLBACK_URI:
        raise LinkedInOfficialApiError("LOOPBACK_REDIRECT_MISMATCH")
    state = secrets.token_urlsafe(32)
    handler = type("BoundedLinkedInOAuthCallbackHandler", (_OAuthCallbackHandler,), {})
    handler.expected_state = state
    handler.result = {}
    handler.completed = Event()
    server = HTTPServer((CALLBACK_HOST, CALLBACK_PORT), handler)
    server.timeout = min(1.0, max(0.1, timeout_seconds))
    authorization_url = build_authorization_url(
        client_id=str(source["LINKEDIN_CLIENT_ID"]), state=state, redirect_uri=redirect_uri,
    )
    if open_browser:
        browser_opener(authorization_url)
    deadline = _utc_now() + timedelta(seconds=max(1.0, timeout_seconds))
    try:
        while _utc_now() < deadline and not handler.completed.is_set():
            server.handle_request()
    finally:
        server.server_close()
    if not handler.completed.is_set():
        raise LinkedInOfficialApiError("OAUTH_CALLBACK_TIMEOUT")
    if handler.result.get("error"):
        raise LinkedInOfficialApiError(handler.result["error"])
    code = handler.result.pop("code", "")
    token_response = exchange_authorization_code(
        code=code,
        client_id=str(source["LINKEDIN_CLIENT_ID"]),
        client_secret=str(source["LINKEDIN_CLIENT_SECRET"]),
        redirect_uri=redirect_uri,
        opener=opener,
    )
    identity = resolve_member_identity(str(token_response["access_token"]), opener=opener)
    issued_at = _utc_now()
    expires_in = int(token_response.get("expires_in") or 0)
    if expires_in <= 0:
        raise LinkedInOfficialApiError("TOKEN_EXPIRY_UNAVAILABLE")
    raw_scope = str(token_response.get("scope") or "")
    granted_scopes = sorted(set(raw_scope.replace(",", " ").split()) or set(REQUIRED_SCOPES))
    if not set(REQUIRED_SCOPES).issubset(granted_scopes):
        raise LinkedInOfficialApiError("OAUTH_SCOPE_PRODUCT_ACCESS_UNAVAILABLE")
    refresh = str(token_response.get("refresh_token") or "")
    metadata = {
        "schema_version": AUTH_METADATA_VERSION,
        "auth_state": "READY_OFFICIAL_MEMBER_API",
        "granted_scopes": granted_scopes,
        "scope_source": "TOKEN_RESPONSE" if raw_scope else "AUTHORIZED_REQUEST_AND_IDENTITY_PROOF",
        "authorized_at_utc": _iso(issued_at),
        "access_token_expires_at_utc": _iso(issued_at + timedelta(seconds=expires_in)),
        "refresh_token_available": bool(refresh),
        "token_store_binding": TOKEN_STORE_BINDING,
        "member_identity": identity,
        "operator_identity_check": "EXACT_SAFE_DISPLAY_NAME_JIM_PHAM",
        "readback_capability": "OFFICIAL_API_STRICT" if READ_SCOPE in granted_scopes else "READBACK_CAPABILITY_LIMITED",
    }
    credentials = {
        "access_token": str(token_response["access_token"]),
        "refresh_token": refresh or None,
    }
    (token_store or WindowsDpapiTokenStore(auth_root)).write(credentials, metadata)
    return {
        "status": "READY_OFFICIAL_MEMBER_API",
        "access_token_issued": True,
        "access_token_expires_at_utc": metadata["access_token_expires_at_utc"],
        "refresh_token_issued": bool(refresh),
        "granted_scopes": granted_scopes,
        "member_identity": identity,
        "token_store_binding": TOKEN_STORE_BINDING,
        "readback_capability": metadata["readback_capability"],
    }


def build_linkedin_ugc_post_payload(intent: Mapping[str, Any], *, person_urn: str) -> dict[str, Any]:
    if not person_urn.startswith("urn:li:person:"):
        raise LinkedInOfficialApiError("MEMBER_IDENTITY_INVALID")
    text = str(intent.get("payload") or "")
    if not text:
        destination_plan = intent.get("destination_plan")
        if isinstance(destination_plan, Mapping):
            text = str(destination_plan.get("payload") or "")
    if not text or len(text) > 3000:
        raise LinkedInOfficialApiError("LINKEDIN_NATIVE_PACKAGE_INVALID")
    return {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }


def _public_url_for_urn(object_id: str) -> str:
    return "https://www.linkedin.com/feed/update/" + urllib.parse.quote(object_id, safe=":") + "/"


class LinkedInOfficialMemberApiTransportV1:
    """Versioned member transport called only by ``DurablePublicationCoordinator``."""

    def __init__(
        self,
        *,
        auth_root: str | Path = DEFAULT_AUTH_ROOT,
        token_store: WindowsDpapiTokenStore | None = None,
        opener: Callable[..., Any] = urllib.request.urlopen,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.token_store = token_store or WindowsDpapiTokenStore(auth_root)
        self.opener = opener
        self.now = now

    def readiness(self) -> dict[str, Any]:
        try:
            metadata = self.token_store.read_metadata()
        except LinkedInOfficialApiError as exc:
            return {"state": "AUTH_UNAVAILABLE", "authenticated": False, "error_class": exc.classification}
        expires = _parse_time(metadata.get("access_token_expires_at_utc"))
        identity = metadata.get("member_identity") if isinstance(metadata.get("member_identity"), Mapping) else {}
        scopes = set(metadata.get("granted_scopes") or [])
        if not metadata or not expires or not str(identity.get("person_urn") or ""):
            return {"state": "AUTH_UNAVAILABLE", "authenticated": False}
        try:
            self.token_store.read_credentials()
        except LinkedInOfficialApiError as exc:
            return {"state": "AUTH_UNAVAILABLE", "authenticated": False, "error_class": exc.classification}
        remaining = expires - self.now().astimezone(timezone.utc)
        days = max(0, int(remaining.total_seconds() // 86400))
        if remaining.total_seconds() <= 0:
            state, authenticated = "REAUTH_REQUIRED", False
        elif not set(REQUIRED_SCOPES).issubset(scopes):
            state, authenticated = "AUTH_UNAVAILABLE", False
        elif remaining <= timedelta(days=EXPIRING_WITHIN_DAYS):
            state, authenticated = "TOKEN_EXPIRING", True
        else:
            state, authenticated = "READY_OFFICIAL_MEMBER_API", True
        return {
            "state": state,
            "authenticated": authenticated,
            "expiry_at_utc": _iso(expires),
            "days_remaining": days,
            "safe_identity": str(identity.get("display_name") or identity.get("person_urn") or ""),
            "person_urn": str(identity.get("person_urn") or ""),
            "readback_capability": str(metadata.get("readback_capability") or "READBACK_CAPABILITY_LIMITED"),
            "secure_store_binding": str(metadata.get("token_store_binding") or TOKEN_STORE_BINDING),
        }

    def _authorized(self) -> tuple[dict[str, Any], dict[str, Any]]:
        readiness = self.readiness()
        if readiness["state"] in {"REAUTH_REQUIRED", "AUTH_UNAVAILABLE"}:
            raise LinkedInOfficialApiError(
                "AUTH_EXPIRED_OR_REAUTH_REQUIRED" if readiness["state"] == "REAUTH_REQUIRED" else "AUTH_UNAVAILABLE"
            )
        return self.token_store.read_credentials(), self.token_store.read_metadata()

    def publish(self, *, intent: Mapping[str, Any], authorization_context: Mapping[str, Any]) -> dict[str, Any]:
        if str(authorization_context.get("operating_mode") or "") != "AUTONOMOUS_DEFAULT":
            raise LinkedInOfficialApiError("CANONICAL_MACHINE_AUTHORIZATION_INVALID")
        credentials, metadata = self._authorized()
        identity = metadata.get("member_identity") if isinstance(metadata.get("member_identity"), Mapping) else {}
        payload = build_linkedin_ugc_post_payload(intent, person_urn=str(identity.get("person_urn") or ""))
        request = urllib.request.Request(
            UGC_POSTS_ENDPOINT,
            data=json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": "Bearer " + str(credentials["access_token"]),
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
        try:
            status, _body, headers = _request_json(request, timeout_seconds=20.0, opener=self.opener)
        except LinkedInOfficialApiError as exc:
            if exc.http_status in {400, 401, 403, 404, 422}:
                return {
                    "status": "DEFINITE_NO_WRITE", "definite_no_write": True,
                    "reason_code": exc.classification, "adapter_version": TRANSPORT_VERSION,
                }
            raise LinkedInAmbiguousWriteError("UNKNOWN_WRITE") from exc
        object_id = str(headers.get("X-RestLi-Id") or headers.get("x-restli-id") or "")
        if status != 201 or not object_id:
            raise LinkedInAmbiguousWriteError("UNKNOWN_WRITE")
        return {
            "status": "SUCCESS",
            "public_object_id": object_id,
            "public_object_url": _public_url_for_urn(object_id),
            "adapter_version": TRANSPORT_VERSION,
            "official_response_identity_present": True,
        }

    def readback(
        self,
        *,
        public_object_id: Optional[str],
        public_object_url: Optional[str],
        intent: Mapping[str, Any],
    ) -> dict[str, Any]:
        del intent
        try:
            credentials, metadata = self._authorized()
        except LinkedInOfficialApiError as exc:
            return {"status": exc.classification, "verified": False}
        if not public_object_id:
            return {"status": "UNKNOWN_WRITE", "verified": False}
        if READ_SCOPE not in set(metadata.get("granted_scopes") or []):
            return {
                "status": "READBACK_CAPABILITY_LIMITED",
                "verified": False,
                "write_exists": True,
                "public_object_id": public_object_id,
                "public_object_url": public_object_url,
                "readback_source": "OFFICIAL_CREATE_RESPONSE_IDENTITY",
            }
        encoded = urllib.parse.quote(public_object_id, safe="")
        request = urllib.request.Request(
            POSTS_READBACK_ENDPOINT + "/" + encoded,
            method="GET",
            headers={
                "Authorization": "Bearer " + str(credentials["access_token"]),
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": LINKEDIN_READBACK_VERSION,
            },
        )
        try:
            status, payload, _ = _request_json(request, timeout_seconds=15.0, opener=self.opener)
        except LinkedInOfficialApiError as exc:
            if exc.http_status == 404:
                return {"status": "ABSENT_SAFE_TO_RETRY", "verified": False, "write_absent": True}
            if exc.http_status == 403:
                return {"status": "READBACK_CAPABILITY_LIMITED", "verified": False}
            if exc.classification in {
                "AUTH_EXPIRED_OR_REAUTH_REQUIRED", "TRANSPORT_UNAVAILABLE",
            }:
                return {"status": exc.classification, "verified": False}
            return {"status": "UNKNOWN_WRITE", "verified": False}
        observed = str(payload.get("id") or "") if status == 200 else ""
        if status == 200 and observed == public_object_id:
            return {
                "status": "CONFIRMED", "verified": True,
                "public_object_id": observed, "public_object_url": public_object_url,
            }
        return {"status": "UNKNOWN_WRITE", "verified": False}
