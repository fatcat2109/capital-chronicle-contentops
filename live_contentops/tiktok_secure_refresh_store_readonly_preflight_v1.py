"""TikTok refresh-token persistence and read-only identity preflight.

This module is deliberately TikTok- and Windows-specific. Importing it performs no
environment read, Credential Manager access, or network request. All secret-bearing
objects have redacted string representations, and all external effects require an
explicit method call through an injected seam.
"""

from __future__ import annotations

import ctypes
import hmac
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from ctypes import wintypes
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

from live_contentops.tiktok_local_desktop_oauth_pkce_v1 import (
    DEFAULT_HTTP_TIMEOUT_SECONDS,
    FormTokenTransport,
    TikTokAppCredentials,
    TikTokOAuthError,
    TikTokTokenSession,
    read_approved_credentials,
    refresh_token_session,
)


CREDENTIAL_TARGET = "CapitalChronicle.ContentOps/TikTok/Sandbox/primary"
USER_INFO_ENDPOINT = "https://open.tiktokapis.com/v2/user/info/"
USER_INFO_FIELDS = ("open_id", "display_name")
IDENTITY_SCOPE = "user.info.basic"

_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2
_ERROR_NOT_FOUND = 1168
_MAX_CREDENTIAL_BLOB_SIZE = 2560


class TikTokSecureSessionError(RuntimeError):
    """Stable nonsecret failure classification for local/session operations."""

    def __init__(self, classification: str) -> None:
        super().__init__(classification)
        self.classification = classification


@dataclass(frozen=True, repr=False)
class RefreshCredentialSession:
    """The only durable TikTok user credential and its app-scoped identity."""

    refresh_token: str
    open_id: str

    def __post_init__(self) -> None:
        if not self.refresh_token or not self.open_id:
            raise TikTokSecureSessionError("REFRESH_CREDENTIAL_INVALID")

    def __repr__(self) -> str:
        return "RefreshCredentialSession(REDACTED)"

    __str__ = __repr__


@dataclass(frozen=True, repr=False)
class CredentialRecord:
    """Internal backend record; both fields are private in diagnostics."""

    username: str
    secret: str

    def __repr__(self) -> str:
        return "CredentialRecord(REDACTED)"

    __str__ = __repr__


@dataclass(frozen=True, repr=False)
class IdentityPreflightResult:
    """Secret-free proof shape for the API account-binding hard gate."""

    open_id_match: bool
    display_name_received: bool

    def __repr__(self) -> str:
        return (
            "IdentityPreflightResult("
            f"open_id_match={self.open_id_match}, "
            f"display_name_received={self.display_name_received})"
        )

    __str__ = __repr__


class CredentialStoreBackend(Protocol):
    """Minimal injected Generic Credential backend."""

    def write(self, target: str, *, username: str, secret: str) -> None: ...

    def read(self, target: str) -> CredentialRecord | None: ...

    def delete(self, target: str) -> None: ...


class UserInfoTransport(Protocol):
    """Injected seam for the single read-only identity request."""

    def get_user_info(
        self,
        endpoint: str,
        *,
        fields: tuple[str, ...],
        access_token: str,
        timeout_seconds: float,
    ) -> Mapping[str, Any]: ...


class _FILETIME(ctypes.Structure):
    _fields_ = (("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD))


class _CREDENTIAL_ATTRIBUTEW(ctypes.Structure):
    _fields_ = (
        ("Keyword", wintypes.LPWSTR),
        ("Flags", wintypes.DWORD),
        ("ValueSize", wintypes.DWORD),
        ("Value", ctypes.POINTER(wintypes.BYTE)),
    )


class _CREDENTIALW(ctypes.Structure):
    _fields_ = (
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", _FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.POINTER(_CREDENTIAL_ATTRIBUTEW)),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    )


_PCREDENTIALW = ctypes.POINTER(_CREDENTIALW)


class WindowsCredentialManagerBackend:
    """Native current-user Windows Generic Credential implementation.

    ``CRED_PERSIST_LOCAL_MACHINE`` means the credential persists for future logons
    of the current Windows user on this machine; CredWrite/CredRead still operate in
    the caller's user credential set.
    """

    def __init__(self, *, library: Any | None = None) -> None:
        if sys.platform != "win32":
            raise TikTokSecureSessionError("CREDENTIAL_MANAGER_UNAVAILABLE")
        try:
            self._library = library or ctypes.WinDLL(
                "Advapi32.dll", use_last_error=True
            )
            self._configure_functions()
        except (AttributeError, OSError):
            raise TikTokSecureSessionError("CREDENTIAL_MANAGER_UNAVAILABLE") from None

    def _configure_functions(self) -> None:
        self._cred_write = self._library.CredWriteW
        self._cred_write.argtypes = (
            ctypes.POINTER(_CREDENTIALW),
            wintypes.DWORD,
        )
        self._cred_write.restype = wintypes.BOOL

        self._cred_read = self._library.CredReadW
        self._cred_read.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(_PCREDENTIALW),
        )
        self._cred_read.restype = wintypes.BOOL

        self._cred_delete = self._library.CredDeleteW
        self._cred_delete.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        )
        self._cred_delete.restype = wintypes.BOOL

        self._cred_free = self._library.CredFree
        self._cred_free.argtypes = (ctypes.c_void_p,)
        self._cred_free.restype = None

    def write(self, target: str, *, username: str, secret: str) -> None:
        if not target or not username or not secret:
            raise TikTokSecureSessionError("CREDENTIAL_RECORD_INVALID")
        blob = secret.encode("utf-16-le")
        if len(blob) > _MAX_CREDENTIAL_BLOB_SIZE:
            raise TikTokSecureSessionError("CREDENTIAL_SECRET_TOO_LARGE")
        blob_buffer = ctypes.create_string_buffer(blob)
        credential = _CREDENTIALW()
        credential.Type = _CRED_TYPE_GENERIC
        credential.TargetName = target
        credential.CredentialBlobSize = len(blob)
        credential.CredentialBlob = ctypes.cast(
            blob_buffer, ctypes.POINTER(wintypes.BYTE)
        )
        credential.Persist = _CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = username
        ctypes.set_last_error(0)
        if not self._cred_write(ctypes.byref(credential), 0):
            raise TikTokSecureSessionError("CREDENTIAL_WRITE_FAILED")

    def read(self, target: str) -> CredentialRecord | None:
        pointer = _PCREDENTIALW()
        ctypes.set_last_error(0)
        if not self._cred_read(
            target,
            _CRED_TYPE_GENERIC,
            0,
            ctypes.byref(pointer),
        ):
            if ctypes.get_last_error() == _ERROR_NOT_FOUND:
                return None
            raise TikTokSecureSessionError("CREDENTIAL_READ_FAILED")
        try:
            credential = pointer.contents
            username = str(credential.UserName or "")
            blob_size = int(credential.CredentialBlobSize)
            if not username or blob_size <= 0 or blob_size % 2:
                raise TikTokSecureSessionError("CREDENTIAL_RECORD_CORRUPT")
            raw = ctypes.string_at(credential.CredentialBlob, blob_size)
            try:
                secret = raw.decode("utf-16-le", errors="strict")
            except UnicodeDecodeError:
                raise TikTokSecureSessionError("CREDENTIAL_RECORD_CORRUPT") from None
            if not secret:
                raise TikTokSecureSessionError("CREDENTIAL_RECORD_CORRUPT")
            return CredentialRecord(username=username, secret=secret)
        finally:
            self._cred_free(pointer)

    def delete(self, target: str) -> None:
        ctypes.set_last_error(0)
        if self._cred_delete(target, _CRED_TYPE_GENERIC, 0):
            return
        if ctypes.get_last_error() == _ERROR_NOT_FOUND:
            return
        raise TikTokSecureSessionError("CREDENTIAL_DELETE_FAILED")


class TikTokRefreshCredentialStore:
    """TikTok-specific secure refresh-session store."""

    def __init__(
        self,
        backend: CredentialStoreBackend | None = None,
        *,
        target: str = CREDENTIAL_TARGET,
    ) -> None:
        if not target:
            raise TikTokSecureSessionError("CREDENTIAL_TARGET_INVALID")
        self._backend = backend or WindowsCredentialManagerBackend()
        self.target = target

    def _write_and_confirm(self, session: RefreshCredentialSession) -> None:
        self._backend.write(
            self.target,
            username=session.open_id,
            secret=session.refresh_token,
        )
        record = self._backend.read(self.target)
        if record is None or not hmac.compare_digest(record.username, session.open_id):
            raise TikTokSecureSessionError("CREDENTIAL_WRITE_CONFIRMATION_FAILED")
        if not hmac.compare_digest(record.secret, session.refresh_token):
            raise TikTokSecureSessionError("CREDENTIAL_WRITE_CONFIRMATION_FAILED")

    def store_refresh_session(
        self, session: RefreshCredentialSession
    ) -> RefreshCredentialSession:
        """Persist exactly refresh token + open_id and verify the native write."""

        existing = self._backend.read(self.target)
        if existing is not None and not hmac.compare_digest(
            existing.username, session.open_id
        ):
            raise TikTokSecureSessionError("IDENTITY_OPEN_ID_MISMATCH")
        self._write_and_confirm(session)
        return session

    def load_refresh_session(self) -> RefreshCredentialSession:
        """Load the current user's stored TikTok refresh session explicitly."""

        try:
            record = self._backend.read(self.target)
        except TikTokSecureSessionError as exc:
            if exc.classification == "CREDENTIAL_RECORD_CORRUPT":
                raise TikTokSecureSessionError("CORRUPT_REFRESH_CREDENTIAL") from None
            raise
        if record is None:
            raise TikTokSecureSessionError("MISSING_REFRESH_CREDENTIAL")
        try:
            return RefreshCredentialSession(
                refresh_token=record.secret,
                open_id=record.username,
            )
        except TikTokSecureSessionError:
            raise TikTokSecureSessionError("CORRUPT_REFRESH_CREDENTIAL") from None

    def replace_rotated_refresh_session(
        self,
        stored: RefreshCredentialSession,
        refreshed: TikTokTokenSession,
    ) -> RefreshCredentialSession:
        """Replace a rotated token without deleting the old credential first."""

        if not refreshed.required_scopes_satisfied:
            raise TikTokSecureSessionError("REQUIRED_SCOPES_INCOMPLETE")
        if not hmac.compare_digest(stored.open_id, refreshed.open_id):
            raise TikTokSecureSessionError("IDENTITY_OPEN_ID_MISMATCH")
        replacement = RefreshCredentialSession(
            refresh_token=refreshed.refresh_token,
            open_id=refreshed.open_id,
        )
        if hmac.compare_digest(stored.refresh_token, replacement.refresh_token):
            return stored
        try:
            self._write_and_confirm(replacement)
        except Exception:
            raise TikTokSecureSessionError(
                "REFRESH_ROTATION_PERSISTENCE_FAILED"
            ) from None
        return replacement

    def delete_refresh_session(self) -> None:
        """Delete this exact target and confirm it is absent."""

        try:
            self._backend.delete(self.target)
            if self._backend.read(self.target) is not None:
                raise TikTokSecureSessionError("CREDENTIAL_DELETE_FAILED")
        except Exception:
            raise TikTokSecureSessionError("CREDENTIAL_DELETE_FAILED") from None


class UrllibUserInfoTransport:
    """Bounded read-only GET transport for TikTok user identity."""

    def __init__(self, *, opener: Callable[..., Any] = urllib.request.urlopen) -> None:
        self._opener = opener

    def get_user_info(
        self,
        endpoint: str,
        *,
        fields: tuple[str, ...],
        access_token: str,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        if not access_token:
            raise TikTokSecureSessionError("ACCESS_TOKEN_ABSENT")
        url = endpoint + "?" + urllib.parse.urlencode({"fields": ",".join(fields)})
        request = urllib.request.Request(
            url,
            headers={"Authorization": "Bearer " + access_token},
            method="GET",
        )
        try:
            with self._opener(request, timeout=timeout_seconds) as response:
                status = int(getattr(response, "status", response.getcode()))
                raw = response.read()
        except urllib.error.HTTPError:
            raise TikTokSecureSessionError("USER_INFO_HTTP_ERROR") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise TikTokSecureSessionError("USER_INFO_TRANSPORT_UNAVAILABLE") from None
        if status != 200:
            raise TikTokSecureSessionError("USER_INFO_HTTP_ERROR")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise TikTokSecureSessionError(
                "USER_INFO_RESPONSE_MALFORMED_JSON"
            ) from None
        if not isinstance(payload, dict):
            raise TikTokSecureSessionError("USER_INFO_RESPONSE_MALFORMED_JSON")
        return payload


def readonly_identity_preflight(
    session: TikTokTokenSession,
    *,
    transport: UserInfoTransport,
    timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> IdentityPreflightResult:
    """Verify the API identity equals the OAuth/token-session open_id."""

    if IDENTITY_SCOPE not in session.granted_scopes:
        raise TikTokSecureSessionError("IDENTITY_SCOPE_MISSING")
    payload = transport.get_user_info(
        USER_INFO_ENDPOINT,
        fields=USER_INFO_FIELDS,
        access_token=session.access_token,
        timeout_seconds=timeout_seconds,
    )
    error = payload.get("error")
    if not isinstance(error, Mapping) or error.get("code") != "ok":
        raise TikTokSecureSessionError("USER_INFO_API_ERROR")
    data = payload.get("data")
    if not isinstance(data, Mapping) or not isinstance(data.get("user"), Mapping):
        raise TikTokSecureSessionError("USER_INFO_RESPONSE_MALFORMED")
    user = data["user"]
    returned_open_id = user.get("open_id")
    if not isinstance(returned_open_id, str) or not returned_open_id:
        raise TikTokSecureSessionError("USER_INFO_OPEN_ID_MISSING")
    if not hmac.compare_digest(returned_open_id, session.open_id):
        raise TikTokSecureSessionError("IDENTITY_OPEN_ID_MISMATCH")
    display_name = user.get("display_name")
    return IdentityPreflightResult(
        open_id_match=True,
        display_name_received=isinstance(display_name, str) and bool(display_name),
    )


def _redacted_success_receipt(
    *,
    identity: IdentityPreflightResult,
    oauth_success: bool,
    refresh_success: bool,
    credential_target: str,
) -> dict[str, Any]:
    return {
        "result": "TIKTOK_SECURE_REFRESH_AND_IDENTITY_PREFLIGHT_READY",
        "oauth_success": oauth_success,
        "refresh_success": refresh_success,
        "state_validated": oauth_success,
        "required_scopes_satisfied": True,
        "identity_preflight_success": True,
        "open_id_match": identity.open_id_match,
        "display_name_received": identity.display_name_received,
        "refresh_token_persisted": True,
        "access_token_persisted": False,
        "credential_target": credential_target,
        "environment_mutated": False,
        "content_posting_calls": 0,
        "media_uploads": 0,
        "public_writes": 0,
    }


def validate_redacted_receipt(
    receipt: Mapping[str, Any],
    *,
    secret_values: tuple[str, ...],
) -> dict[str, Any]:
    """Fail closed if a known in-memory secret entered a receipt."""

    serialized = json.dumps(dict(receipt), sort_keys=True, ensure_ascii=True)
    if any(secret and secret in serialized for secret in secret_values):
        raise TikTokSecureSessionError("SECRET_MATERIAL_IN_RECEIPT")
    return dict(receipt)


def persist_supervised_session_after_preflight(
    session: TikTokTokenSession,
    *,
    store: TikTokRefreshCredentialStore,
    user_info_transport: UserInfoTransport,
) -> dict[str, Any]:
    """Future supervised flow: preflight first, then persist only refresh + open_id."""

    if not session.required_scopes_satisfied:
        raise TikTokSecureSessionError("REQUIRED_SCOPES_INCOMPLETE")
    identity = readonly_identity_preflight(session, transport=user_info_transport)
    store.store_refresh_session(
        RefreshCredentialSession(
            refresh_token=session.refresh_token,
            open_id=session.open_id,
        )
    )
    receipt = _redacted_success_receipt(
        identity=identity,
        oauth_success=True,
        refresh_success=False,
        credential_target=store.target,
    )
    return validate_redacted_receipt(
        receipt,
        secret_values=(session.access_token, session.refresh_token, session.open_id),
    )


def refresh_stored_session_and_preflight(
    *,
    store: TikTokRefreshCredentialStore,
    token_transport: FormTokenTransport,
    user_info_transport: UserInfoTransport,
    env: Mapping[str, str],
) -> dict[str, Any]:
    """Future noninteractive flow with safe refresh-token rotation."""

    stored = store.load_refresh_session()
    credentials: TikTokAppCredentials = read_approved_credentials(env)
    try:
        refreshed = refresh_token_session(
            credentials,
            stored.refresh_token,
            transport=token_transport,
        )
    except TikTokOAuthError:
        raise
    if not refreshed.required_scopes_satisfied:
        raise TikTokSecureSessionError("REQUIRED_SCOPES_INCOMPLETE")
    if not hmac.compare_digest(stored.open_id, refreshed.open_id):
        raise TikTokSecureSessionError("IDENTITY_OPEN_ID_MISMATCH")
    store.replace_rotated_refresh_session(stored, refreshed)
    identity = readonly_identity_preflight(
        refreshed,
        transport=user_info_transport,
    )
    receipt = _redacted_success_receipt(
        identity=identity,
        oauth_success=False,
        refresh_success=True,
        credential_target=store.target,
    )
    return validate_redacted_receipt(
        receipt,
        secret_values=(
            credentials.client_key,
            credentials.client_secret,
            stored.refresh_token,
            stored.open_id,
            refreshed.access_token,
            refreshed.refresh_token,
            refreshed.open_id,
        ),
    )
