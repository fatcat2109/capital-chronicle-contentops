"""Exact one-shot TikTok Sandbox draft-delivery canary.

Importing this module performs no environment read, Credential Manager access, media
probe, or network request.  The only live-capable entrypoint is the separately gated CLI.
The canary is deliberately TikTok-specific and stops at ``SEND_TO_USER_INBOX``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from live_contentops.tiktok_local_desktop_oauth_pkce_v1 import (
    FormTokenTransport,
    TikTokOAuthError,
    TikTokTokenSession,
    read_approved_credentials,
    refresh_token_session,
)
from live_contentops.tiktok_secure_refresh_store_readonly_preflight_v1 import (
    TikTokRefreshCredentialStore,
    TikTokSecureSessionError,
    UserInfoTransport,
    readonly_identity_preflight,
)
from video.official_platform_publication_v1.models import load_publication_package


RECEIPT_SCHEMA = "contentops.v2.tiktok_sandbox_draft_canary_receipt.v1"
JOURNAL_SCHEMA = "contentops.v2.tiktok_sandbox_draft_canary_journal.v1"
ATTEMPT_SCHEMA = "contentops.v2.tiktok_sandbox_draft_canary_attempt.v1"

EXACT_PACKAGE_ID = (
    "pkg_2dfe4af587fd8135d04bae456b8c5b30a1560be91232b34f520cf7f05a71c0b2"
)
DESTINATION_ALIAS = "TIKTOK_SANDBOX_PRIMARY"
ENVIRONMENT = "SANDBOX"
DELIVERY_INTENT = "DRAFT_DELIVERY"
CONTENT_POSTING_MODE = "UPLOAD_TO_TIKTOK_DRAFT"
PROVIDER_INTENT_VERSION = "UPLOAD_TO_TIKTOK_DRAFT.v1"
OWNER_AUTHORITY_SCOPE = "ONE_EXACT_TIKTOK_SANDBOX_DRAFT_DELIVERY"

CANONICAL_PACKAGE_MANIFEST = Path(
    r"A:\Capital Chronicle\Worktrees\ContentOps\v2-native-multiformat-multilingual-package-factory-v1"
    r"\.task-runtime\v2-native-multiformat-multilingual-package-factory-v1\packages"
    r"\short.en.pkg_2dfe4af587fd8135d04bae456b8c5b30a1560be91232b34f520cf7f05a71c0b2.json"
)
DEFAULT_JOURNAL_ROOT = (
    Path(__file__).resolve().parents[1]
    / ".task-runtime"
    / "v2-tiktok-sandbox-draft-canary-v1"
    / "journal"
)

INIT_ENDPOINT = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
STATUS_ENDPOINT = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
REQUIRED_SCOPES = frozenset({"user.info.basic", "video.list", "video.upload"})

MIN_CHUNK_BYTES = 5_000_000
MAX_CHUNK_BYTES = 64_000_000
MAX_FINAL_CHUNK_BYTES = 128_000_000
MAX_CHUNKS = 1000
MAX_VIDEO_BYTES = 4_000_000_000
MIN_DIMENSION = 360
MAX_DIMENSION = 4096
MIN_FPS = 23.0
MAX_FPS = 60.0
MAX_DURATION_SECONDS = 600.0


class TikTokCanaryError(RuntimeError):
    """Stable nonsecret failure classification."""

    def __init__(self, classification: str) -> None:
        super().__init__(classification)
        self.classification = classification


class ProviderCallError(TikTokCanaryError):
    """Provider failure with an explicit acceptance-ambiguity bit."""

    def __init__(self, classification: str, *, ambiguous: bool) -> None:
        super().__init__(classification)
        self.ambiguous = ambiguous


class CanarySecurePreflightError(TikTokCanaryError):
    """A redacted secure-preflight failure with truthful completed-step flags."""

    def __init__(
        self,
        classification: str,
        *,
        oauth_refresh_success: bool,
        identity_preflight_success: bool,
        required_scopes_satisfied: bool,
        refresh_token_rotation_persisted: bool,
    ) -> None:
        super().__init__(classification)
        self.oauth_refresh_success = oauth_refresh_success
        self.identity_preflight_success = identity_preflight_success
        self.required_scopes_satisfied = required_scopes_satisfied
        self.refresh_token_rotation_persisted = refresh_token_rotation_persisted


@dataclass(frozen=True)
class PackageAuthority:
    package_id: str
    media_path: Path
    media_sha256: str
    manifest_size_bytes: int


@dataclass(frozen=True)
class ChunkRange:
    first_byte: int
    last_byte: int
    total_bytes: int

    @property
    def length(self) -> int:
        return self.last_byte - self.first_byte + 1


@dataclass(frozen=True)
class MediaPreflight:
    package_id: str
    media_path: Path
    media_sha256: str
    size_bytes: int
    container: str
    codec: str
    width: int
    height: int
    fps: float
    duration_seconds: float
    chunks: tuple[ChunkRange, ...]

    @property
    def source_info(self) -> dict[str, int | str]:
        return {
            "source": "FILE_UPLOAD",
            "video_size": self.size_bytes,
            "chunk_size": self.chunks[0].length,
            "total_chunk_count": len(self.chunks),
        }

    def nonsecret_metadata(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "media_sha256": self.media_sha256,
            "size_bytes": self.size_bytes,
            "container": self.container,
            "codec": self.codec,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "duration_seconds": self.duration_seconds,
            "chunk_size": self.chunks[0].length,
            "total_chunk_count": len(self.chunks),
        }


@dataclass(frozen=True, repr=False)
class CanarySecurityContext:
    access_token: str
    oauth_refresh_success: bool
    identity_preflight_success: bool
    required_scopes_satisfied: bool
    refresh_token_rotation_persisted: bool

    def __repr__(self) -> str:
        return "CanarySecurityContext(REDACTED_IN_MEMORY_ONLY)"

    __str__ = __repr__


@dataclass(frozen=True, repr=False)
class ProviderInitResult:
    publish_id: str
    upload_url: str

    def __repr__(self) -> str:
        return "ProviderInitResult(publish_id_present=True, upload_url=REDACTED)"

    __str__ = __repr__


class SecureSessionProvider(Protocol):
    def refresh_and_preflight(self) -> CanarySecurityContext: ...


class TikTokCanaryTransport(Protocol):
    def initialize_draft(
        self, *, access_token: str, source_info: Mapping[str, Any]
    ) -> ProviderInitResult: ...

    def upload_chunk(
        self,
        *,
        upload_url: str,
        chunk: bytes,
        byte_range: ChunkRange,
        final_chunk: bool,
    ) -> None: ...

    def fetch_status(
        self, *, access_token: str, publish_id: str
    ) -> Mapping[str, Any]: ...


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def deterministic_canary_attempt_id(
    *, package_id: str, media_sha256: str
) -> str:
    payload = {
        "schema": ATTEMPT_SCHEMA,
        "package_id": package_id,
        "media_sha256": media_sha256,
        "destination_alias": DESTINATION_ALIAS,
        "environment": ENVIRONMENT,
        "delivery_intent": DELIVERY_INTENT,
        "provider_intent_version": PROVIDER_INTENT_VERSION,
    }
    return "ttcanary_" + hashlib.sha256(_canonical_json(payload)).hexdigest()


def build_chunk_plan(size_bytes: int) -> tuple[ChunkRange, ...]:
    """Derive TikTok's current sequential FILE_UPLOAD contract from actual bytes."""

    if size_bytes <= 0 or size_bytes > MAX_VIDEO_BYTES:
        raise TikTokCanaryError("MEDIA_SIZE_RESTRICTION_FAILURE")
    if size_bytes <= MAX_CHUNK_BYTES:
        return (ChunkRange(0, size_bytes - 1, size_bytes),)

    chunk_size = min(MAX_CHUNK_BYTES, size_bytes // 2)
    if chunk_size < MIN_CHUNK_BYTES:
        raise TikTokCanaryError("INVALID_CHUNK_CONTRACT")
    total_chunk_count = size_bytes // chunk_size
    if not 2 <= total_chunk_count <= MAX_CHUNKS:
        raise TikTokCanaryError("INVALID_CHUNK_CONTRACT")

    chunks: list[ChunkRange] = []
    offset = 0
    for index in range(total_chunk_count):
        remaining = size_bytes - offset
        length = remaining if index == total_chunk_count - 1 else chunk_size
        if index < total_chunk_count - 1 and not MIN_CHUNK_BYTES <= length <= MAX_CHUNK_BYTES:
            raise TikTokCanaryError("INVALID_CHUNK_CONTRACT")
        if index == total_chunk_count - 1 and not MIN_CHUNK_BYTES <= length <= MAX_FINAL_CHUNK_BYTES:
            raise TikTokCanaryError("INVALID_CHUNK_CONTRACT")
        chunks.append(ChunkRange(offset, offset + length - 1, size_bytes))
        offset += length
    if offset != size_bytes:
        raise TikTokCanaryError("INVALID_CHUNK_CONTRACT")
    return tuple(chunks)


class AcceptedShortPackageResolver:
    """Resolve only the owner-selected accepted Short manifest; no CLI path input."""

    def __init__(self, manifest_path: Path = CANONICAL_PACKAGE_MANIFEST) -> None:
        self.manifest_path = manifest_path

    def describe_authority(self) -> PackageAuthority:
        if not self.manifest_path.is_file():
            raise TikTokCanaryError("CANONICAL_PACKAGE_MISSING")
        try:
            package = load_publication_package(self.manifest_path)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError):
            raise TikTokCanaryError("CANONICAL_PACKAGE_INVALID") from None
        if package.get("package_id") != EXACT_PACKAGE_ID:
            raise TikTokCanaryError("PACKAGE_ID_MISMATCH")
        if package.get("format") != "SHORT_9_16" or package.get("language") != "en":
            raise TikTokCanaryError("CANONICAL_PACKAGE_INVALID")
        if "TIKTOK" not in package.get("intended_future_surfaces", []):
            raise TikTokCanaryError("CANONICAL_PACKAGE_INVALID")
        media = package["artifacts"].get("clean_video")
        if not isinstance(media, Mapping):
            raise TikTokCanaryError("CANONICAL_PACKAGE_INVALID")
        try:
            media_path = Path(str(media["path"]))
            media_sha256 = str(media["sha256"])
            manifest_size = int(media["size_bytes"])
        except (KeyError, TypeError, ValueError):
            raise TikTokCanaryError("CANONICAL_PACKAGE_INVALID") from None
        if len(media_sha256) != 64 or any(c not in "0123456789abcdef" for c in media_sha256):
            raise TikTokCanaryError("CANONICAL_PACKAGE_INVALID")
        return PackageAuthority(
            package_id=EXACT_PACKAGE_ID,
            media_path=media_path,
            media_sha256=media_sha256,
            manifest_size_bytes=manifest_size,
        )

    def validate_media(
        self,
        authority: PackageAuthority,
        *,
        probe: Callable[[Path], Mapping[str, Any]],
    ) -> MediaPreflight:
        path = authority.media_path
        if not path.is_file():
            raise TikTokCanaryError("CANONICAL_MEDIA_MISSING")
        actual_size = path.stat().st_size
        if actual_size != authority.manifest_size_bytes:
            raise TikTokCanaryError("MEDIA_SIZE_MISMATCH")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if not hmac.compare_digest(digest.hexdigest(), authority.media_sha256):
            raise TikTokCanaryError("MEDIA_HASH_MISMATCH")
        try:
            data = dict(probe(path))
            container = str(data["container"])
            codec = str(data["codec"])
            width = int(data["width"])
            height = int(data["height"])
            fps = float(data["fps"])
            duration = float(data["duration_seconds"])
        except (KeyError, TypeError, ValueError):
            raise TikTokCanaryError("MEDIA_PROBE_INVALID") from None
        if path.suffix.casefold() != ".mp4" or "mp4" not in container.casefold():
            raise TikTokCanaryError("MEDIA_FORMAT_RESTRICTION_FAILURE")
        if codec.casefold() != "h264":
            raise TikTokCanaryError("MEDIA_CODEC_RESTRICTION_FAILURE")
        if not (MIN_DIMENSION <= width <= MAX_DIMENSION):
            raise TikTokCanaryError("MEDIA_DIMENSION_RESTRICTION_FAILURE")
        if not (MIN_DIMENSION <= height <= MAX_DIMENSION):
            raise TikTokCanaryError("MEDIA_DIMENSION_RESTRICTION_FAILURE")
        if not (MIN_FPS <= fps <= MAX_FPS):
            raise TikTokCanaryError("MEDIA_FPS_RESTRICTION_FAILURE")
        if not (0 < duration <= MAX_DURATION_SECONDS):
            raise TikTokCanaryError("MEDIA_DURATION_RESTRICTION_FAILURE")
        chunks = build_chunk_plan(actual_size)
        return MediaPreflight(
            package_id=authority.package_id,
            media_path=path,
            media_sha256=authority.media_sha256,
            size_bytes=actual_size,
            container=container,
            codec=codec,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration,
            chunks=chunks,
        )


def ffprobe_media(path: Path) -> Mapping[str, Any]:
    """Read only technical media metadata; never transcode or rerender."""

    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=format_name,duration:stream=codec_type,codec_name,width,height,avg_frame_rate",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        payload = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        raise TikTokCanaryError("MEDIA_PROBE_FAILED") from None
    streams = payload.get("streams", [])
    video = next(
        (item for item in streams if item.get("codec_type") == "video"), None
    )
    if not isinstance(video, Mapping):
        raise TikTokCanaryError("MEDIA_VIDEO_STREAM_MISSING")
    rate = str(video.get("avg_frame_rate") or "")
    try:
        numerator, denominator = rate.split("/", 1)
        fps = float(numerator) / float(denominator)
    except (ValueError, ZeroDivisionError):
        raise TikTokCanaryError("MEDIA_PROBE_INVALID") from None
    format_data = payload.get("format", {})
    return {
        "container": str(format_data.get("format_name") or ""),
        "codec": str(video.get("codec_name") or ""),
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": fps,
        "duration_seconds": format_data.get("duration"),
    }


class AcceptedSecureSessionProvider:
    """Reuse accepted secure store/OAuth/identity primitives for one transient session."""

    def __init__(
        self,
        *,
        store: TikTokRefreshCredentialStore,
        token_transport: FormTokenTransport,
        user_info_transport: UserInfoTransport,
        env: Mapping[str, str],
    ) -> None:
        self._store = store
        self._token_transport = token_transport
        self._user_info_transport = user_info_transport
        self._env = env

    def refresh_and_preflight(self) -> CanarySecurityContext:
        stored = self._store.load_refresh_session()
        credentials = read_approved_credentials(self._env)
        try:
            refreshed: TikTokTokenSession = refresh_token_session(
                credentials,
                stored.refresh_token,
                transport=self._token_transport,
            )
        except TikTokOAuthError as exc:
            raise CanarySecurePreflightError(
                exc.classification,
                oauth_refresh_success=False,
                identity_preflight_success=False,
                required_scopes_satisfied=False,
                refresh_token_rotation_persisted=False,
            ) from None
        if not REQUIRED_SCOPES.issubset(refreshed.granted_scopes):
            raise CanarySecurePreflightError(
                "REQUIRED_SCOPES_INCOMPLETE",
                oauth_refresh_success=True,
                identity_preflight_success=False,
                required_scopes_satisfied=False,
                refresh_token_rotation_persisted=False,
            )
        if not hmac.compare_digest(stored.open_id, refreshed.open_id):
            raise CanarySecurePreflightError(
                "IDENTITY_OPEN_ID_MISMATCH",
                oauth_refresh_success=True,
                identity_preflight_success=False,
                required_scopes_satisfied=True,
                refresh_token_rotation_persisted=False,
            )
        rotated = not hmac.compare_digest(
            stored.refresh_token, refreshed.refresh_token
        )
        try:
            self._store.replace_rotated_refresh_session(stored, refreshed)
        except TikTokSecureSessionError as exc:
            raise CanarySecurePreflightError(
                exc.classification,
                oauth_refresh_success=True,
                identity_preflight_success=False,
                required_scopes_satisfied=True,
                refresh_token_rotation_persisted=False,
            ) from None
        try:
            identity = readonly_identity_preflight(
                refreshed, transport=self._user_info_transport
            )
        except TikTokSecureSessionError as exc:
            raise CanarySecurePreflightError(
                exc.classification,
                oauth_refresh_success=True,
                identity_preflight_success=False,
                required_scopes_satisfied=True,
                refresh_token_rotation_persisted=rotated,
            ) from None
        if not identity.open_id_match:
            raise CanarySecurePreflightError(
                "IDENTITY_OPEN_ID_MISMATCH",
                oauth_refresh_success=True,
                identity_preflight_success=False,
                required_scopes_satisfied=True,
                refresh_token_rotation_persisted=rotated,
            )
        return CanarySecurityContext(
            access_token=refreshed.access_token,
            oauth_refresh_success=True,
            identity_preflight_success=True,
            required_scopes_satisfied=True,
            refresh_token_rotation_persisted=rotated,
        )


class UrllibTikTokCanaryTransport:
    """One-attempt official TikTok transport with no automatic HTTP retries."""

    def __init__(
        self,
        *,
        opener: Callable[..., Any] | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._opener = opener or urllib.request.build_opener(
            _NoRedirectHandler()
        ).open
        self._timeout_seconds = timeout_seconds

    def _post_json(
        self,
        endpoint: str,
        *,
        access_token: str,
        body: Mapping[str, Any],
        mutation: bool,
        operation: str,
    ) -> Mapping[str, Any]:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(dict(body), separators=(",", ":")).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + access_token,
                "Content-Type": "application/json; charset=UTF-8",
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                status = int(getattr(response, "status", response.getcode()))
                raw = response.read()
        except urllib.error.HTTPError as exc:
            ambiguous = mutation and int(exc.code) >= 500
            raise ProviderCallError(
                f"{operation}_HTTP_PROVIDER_ERROR", ambiguous=ambiguous
            ) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProviderCallError(
                f"{operation}_TRANSPORT_UNAVAILABLE", ambiguous=mutation
            ) from None
        if status != 200:
            raise ProviderCallError(
                f"{operation}_HTTP_PROVIDER_ERROR",
                ambiguous=mutation and status >= 500,
            )
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderCallError(
                f"{operation}_RESPONSE_MALFORMED", ambiguous=mutation
            ) from None
        if not isinstance(payload, Mapping):
            raise ProviderCallError(
                f"{operation}_RESPONSE_MALFORMED", ambiguous=mutation
            )
        return payload

    def initialize_draft(
        self, *, access_token: str, source_info: Mapping[str, Any]
    ) -> ProviderInitResult:
        payload = self._post_json(
            INIT_ENDPOINT,
            access_token=access_token,
            body={"source_info": dict(source_info)},
            mutation=True,
            operation="INIT",
        )
        error = payload.get("error")
        if not isinstance(error, Mapping) or error.get("code") != "ok":
            raise ProviderCallError("INIT_PROVIDER_ERROR", ambiguous=False)
        data = payload.get("data")
        if not isinstance(data, Mapping):
            raise ProviderCallError("INIT_RESPONSE_MISSING_DATA", ambiguous=True)
        publish_id = str(data.get("publish_id") or "")
        upload_url = str(data.get("upload_url") or "")
        if not re.fullmatch(r"[A-Za-z0-9._~:-]{1,64}", publish_id) or not upload_url:
            raise ProviderCallError("INIT_RESPONSE_MISSING_PROVIDER_REFS", ambiguous=True)
        _validate_transient_upload_url(upload_url)
        return ProviderInitResult(publish_id=publish_id, upload_url=upload_url)

    def upload_chunk(
        self,
        *,
        upload_url: str,
        chunk: bytes,
        byte_range: ChunkRange,
        final_chunk: bool,
    ) -> None:
        _validate_transient_upload_url(upload_url)
        if len(chunk) != byte_range.length:
            raise TikTokCanaryError("LOCAL_CHUNK_LENGTH_MISMATCH")
        request = urllib.request.Request(
            upload_url,
            data=chunk,
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(byte_range.length),
                "Content-Range": (
                    f"bytes {byte_range.first_byte}-{byte_range.last_byte}/"
                    f"{byte_range.total_bytes}"
                ),
            },
            method="PUT",
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                status = int(getattr(response, "status", response.getcode()))
                response.read()
        except urllib.error.HTTPError as exc:
            raise ProviderCallError(
                "MEDIA_TRANSFER_HTTP_PROVIDER_ERROR",
                ambiguous=int(exc.code) >= 500,
            ) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProviderCallError(
                "MEDIA_TRANSFER_TRANSPORT_UNAVAILABLE", ambiguous=True
            ) from None
        expected_status = 201 if final_chunk else 206
        if status != expected_status:
            raise ProviderCallError(
                "MEDIA_TRANSFER_UNEXPECTED_HTTP_STATUS", ambiguous=status >= 500
            )

    def fetch_status(
        self, *, access_token: str, publish_id: str
    ) -> Mapping[str, Any]:
        payload = self._post_json(
            STATUS_ENDPOINT,
            access_token=access_token,
            body={"publish_id": publish_id},
            mutation=False,
            operation="STATUS",
        )
        error = payload.get("error")
        if not isinstance(error, Mapping) or error.get("code") != "ok":
            raise ProviderCallError("STATUS_PROVIDER_ERROR", ambiguous=False)
        data = payload.get("data")
        if not isinstance(data, Mapping):
            raise ProviderCallError("STATUS_RESPONSE_MALFORMED", ambiguous=False)
        return dict(data)


def _validate_transient_upload_url(upload_url: str) -> None:
    parsed = urllib.parse.urlsplit(upload_url)
    hostname = (parsed.hostname or "").casefold()
    if (
        parsed.scheme != "https"
        or not hostname.endswith(".tiktokapis.com")
        or not parsed.query
        or parsed.fragment
    ):
        raise ProviderCallError("UPLOAD_URL_REJECTED", ambiguous=True)


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Fail closed instead of forwarding tokens or media across redirects."""

    def redirect_request(
        self,
        req: Any,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


class CanaryJournal:
    """Atomic nonsecret attempt journal that prevents blind second delivery."""

    def __init__(self, root: Path = DEFAULT_JOURNAL_ROOT) -> None:
        self.root = root

    def path_for(self, attempt_id: str) -> Path:
        if not attempt_id.startswith("ttcanary_"):
            raise TikTokCanaryError("ATTEMPT_ID_INVALID")
        return self.root / f"{attempt_id}.json"

    def load(self, attempt_id: str) -> dict[str, Any] | None:
        path = self.path_for(attempt_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise TikTokCanaryError("CANARY_JOURNAL_CORRUPT") from None
        if data.get("schema") != JOURNAL_SCHEMA or data.get("attempt_id") != attempt_id:
            raise TikTokCanaryError("CANARY_JOURNAL_CORRUPT")
        _assert_journal_is_redacted(data)
        return data

    def create_intent(self, prepared: MediaPreflight, attempt_id: str) -> dict[str, Any]:
        if self.load(attempt_id) is not None:
            raise TikTokCanaryError("EXISTING_ATTEMPT_PREVENTS_DUPLICATE_CANARY")
        now = _utc_now()
        data = {
            "schema": JOURNAL_SCHEMA,
            "attempt_id": attempt_id,
            "package_id": prepared.package_id,
            "media_sha256": prepared.media_sha256,
            "destination_alias": DESTINATION_ALIAS,
            "state": "INTENT_RECORDED",
            "publish_id": None,
            "uploaded_bytes": 0,
            "last_provider_status": None,
            "terminal_classification": None,
            "created_at": now,
            "updated_at": now,
        }
        self._write_new(attempt_id, data)
        return data

    def update(self, data: Mapping[str, Any], **changes: Any) -> dict[str, Any]:
        updated = dict(data)
        updated.update(changes)
        updated["updated_at"] = _utc_now()
        self._write(str(updated["attempt_id"]), updated)
        return updated

    def _write(self, attempt_id: str, data: Mapping[str, Any]) -> None:
        _assert_journal_is_redacted(data)
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.path_for(attempt_id)
        temporary = path.with_suffix(".json.tmp")
        encoded = json.dumps(dict(data), indent=2, sort_keys=True) + "\n"
        try:
            temporary.write_text(encoded, encoding="utf-8")
            os.replace(temporary, path)
        except OSError:
            raise TikTokCanaryError("CANARY_JOURNAL_WRITE_FAILED") from None

    def _write_new(self, attempt_id: str, data: Mapping[str, Any]) -> None:
        _assert_journal_is_redacted(data)
        self.root.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(dict(data), indent=2, sort_keys=True) + "\n"
        try:
            with self.path_for(attempt_id).open("x", encoding="utf-8") as stream:
                stream.write(encoded)
        except FileExistsError:
            raise TikTokCanaryError(
                "EXISTING_ATTEMPT_PREVENTS_DUPLICATE_CANARY"
            ) from None
        except OSError:
            raise TikTokCanaryError("CANARY_JOURNAL_WRITE_FAILED") from None


_FORBIDDEN_SERIALIZED_KEYS = {
    "client_key",
    "client_secret",
    "access_token",
    "refresh_token",
    "open_id",
    "authorization",
    "upload_url",
    "upload_token",
}


def _assert_journal_is_redacted(value: Mapping[str, Any]) -> None:
    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if str(key).casefold() in _FORBIDDEN_SERIALIZED_KEYS:
                    raise TikTokCanaryError("SECRET_MATERIAL_IN_CANARY_ARTIFACT")
                walk(child)
        elif isinstance(item, Sequence) and not isinstance(
            item, (str, bytes, bytearray)
        ):
            for child in item:
                walk(child)

    walk(value)
    serialized = json.dumps(dict(value), sort_keys=True).casefold()
    if "authorization: bearer" in serialized or "upload_token=" in serialized:
        raise TikTokCanaryError("SECRET_MATERIAL_IN_CANARY_ARTIFACT")


def _base_receipt(
    *,
    attempt_id: str,
    package_id: str,
    media_sha256: str,
    result: str,
) -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "result": result,
        "attempt_id": attempt_id,
        "package_id": package_id,
        "media_sha256": media_sha256,
        "destination_alias": DESTINATION_ALIAS,
        "environment": ENVIRONMENT,
        "delivery_intent": DELIVERY_INTENT,
        "owner_authority_scope": OWNER_AUTHORITY_SCOPE,
        "oauth_refresh_success": False,
        "identity_preflight_success": False,
        "required_scopes_satisfied": False,
        "logical_draft_delivery_attempts": 0,
        "mutation_http_calls": 0,
        "status_readback_calls": 0,
        "publish_id_present": False,
        "terminal_provider_status": None,
        "draft_delivery_confirmed": False,
        "creator_finalization_required": True,
        "creator_finalization_observed": False,
        "public_post_confirmed": False,
        "access_token_persisted": False,
        "refresh_token_rotation_persisted": False,
        "unknown_write": False,
        "content_posting_mode": CONTENT_POSTING_MODE,
        "public_writes": 0,
        "v1_mutations": 0,
        "scheduler_mutations": 0,
    }


def validate_redacted_canary_receipt(
    receipt: Mapping[str, Any], *, secret_values: Sequence[str] = ()
) -> dict[str, Any]:
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise TikTokCanaryError("CANARY_RECEIPT_INVALID")
    if receipt.get("access_token_persisted") is not False:
        raise TikTokCanaryError("ACCESS_TOKEN_PERSISTENCE_FORBIDDEN")
    serialized = json.dumps(dict(receipt), sort_keys=True, ensure_ascii=True)
    lowered = serialized.casefold()
    if "authorization: bearer" in lowered or "upload_token=" in lowered:
        raise TikTokCanaryError("SECRET_MATERIAL_IN_CANARY_ARTIFACT")
    if any(secret and secret in serialized for secret in secret_values):
        raise TikTokCanaryError("SECRET_MATERIAL_IN_CANARY_ARTIFACT")
    return dict(receipt)


class TikTokSandboxDraftCanaryExecutor:
    """Coordinate exactly one authorized logical draft delivery or readback-only resume."""

    def __init__(
        self,
        *,
        resolver: AcceptedShortPackageResolver,
        secure_session_provider: SecureSessionProvider,
        transport: TikTokCanaryTransport,
        journal: CanaryJournal,
        media_probe: Callable[[Path], Mapping[str, Any]] = ffprobe_media,
        poll_schedule_seconds: Sequence[float] = (0.0, 2.0, 5.0, 10.0, 20.0),
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._resolver = resolver
        self._secure_session_provider = secure_session_provider
        self._transport = transport
        self._journal = journal
        self._media_probe = media_probe
        self._poll_schedule_seconds = tuple(poll_schedule_seconds)
        self._sleeper = sleeper

    def expected_attempt(self) -> tuple[PackageAuthority, str]:
        authority = self._resolver.describe_authority()
        attempt_id = deterministic_canary_attempt_id(
            package_id=authority.package_id,
            media_sha256=authority.media_sha256,
        )
        return authority, attempt_id

    def run(
        self,
        *,
        authorized_attempt_id: str,
        readback_only: bool = False,
    ) -> dict[str, Any]:
        authority: PackageAuthority | None = None
        attempt_id = ""
        receipt = _base_receipt(
            attempt_id="",
            package_id=EXACT_PACKAGE_ID,
            media_sha256="",
            result="CANARY_NOT_STARTED",
        )
        secrets: tuple[str, ...] = ()
        try:
            authority, attempt_id = self.expected_attempt()
            receipt.update(
                attempt_id=attempt_id,
                package_id=authority.package_id,
                media_sha256=authority.media_sha256,
            )
            if not authorized_attempt_id or not hmac.compare_digest(
                authorized_attempt_id, attempt_id
            ):
                raise TikTokCanaryError("OWNER_AUTHORIZED_ATTEMPT_ID_MISMATCH")

            existing = self._journal.load(attempt_id)
            if readback_only:
                if existing is None or not existing.get("publish_id"):
                    raise TikTokCanaryError("READBACK_ONLY_ATTEMPT_NOT_RESUMABLE")
                if existing.get("state") in {
                    "DRAFT_DELIVERY_CONFIRMED",
                    "FAILED",
                }:
                    raise TikTokCanaryError("EXISTING_ATTEMPT_ALREADY_TERMINAL")
                receipt["logical_draft_delivery_attempts"] = 1
            elif existing is not None:
                if existing.get("state") in {
                    "DRAFT_DELIVERY_CONFIRMED",
                    "FAILED",
                }:
                    raise TikTokCanaryError("EXISTING_ATTEMPT_ALREADY_TERMINAL")
                raise TikTokCanaryError("EXISTING_ATTEMPT_PREVENTS_DUPLICATE_CANARY")

            security = self._secure_session_provider.refresh_and_preflight()
            secrets = (security.access_token,)
            receipt.update(
                oauth_refresh_success=security.oauth_refresh_success,
                identity_preflight_success=security.identity_preflight_success,
                required_scopes_satisfied=security.required_scopes_satisfied,
                refresh_token_rotation_persisted=(
                    security.refresh_token_rotation_persisted
                ),
            )
            if not (
                security.oauth_refresh_success
                and security.identity_preflight_success
                and security.required_scopes_satisfied
            ):
                raise TikTokCanaryError("SECURE_IDENTITY_PREFLIGHT_FAILED")

            if readback_only:
                return self._poll_status(
                    access_token=security.access_token,
                    journal_data=dict(existing),
                    receipt=receipt,
                    transfer_was_ambiguous=True,
                    secret_values=secrets,
                )

            prepared = self._resolver.validate_media(
                authority, probe=self._media_probe
            )
            journal_data = self._journal.create_intent(prepared, attempt_id)
            receipt["logical_draft_delivery_attempts"] = 1

            try:
                receipt["mutation_http_calls"] += 1
                init = self._transport.initialize_draft(
                    access_token=security.access_token,
                    source_info=prepared.source_info,
                )
            except ProviderCallError as exc:
                state = "UNKNOWN_WRITE" if exc.ambiguous else "FAILED"
                journal_data = self._journal.update(
                    journal_data,
                    state=state,
                    terminal_classification=exc.classification,
                )
                receipt.update(
                    result=exc.classification,
                    unknown_write=exc.ambiguous,
                )
                return validate_redacted_canary_receipt(
                    receipt, secret_values=secrets
                )

            journal_data = self._journal.update(
                journal_data,
                state="INITIATED",
                publish_id=init.publish_id,
            )
            receipt["publish_id_present"] = True

            transfer_ambiguous = False
            try:
                with prepared.media_path.open("rb") as media_stream:
                    for index, byte_range in enumerate(prepared.chunks):
                        media_stream.seek(byte_range.first_byte)
                        chunk = media_stream.read(byte_range.length)
                        receipt["mutation_http_calls"] += 1
                        self._transport.upload_chunk(
                            upload_url=init.upload_url,
                            chunk=chunk,
                            byte_range=byte_range,
                            final_chunk=index == len(prepared.chunks) - 1,
                        )
                        journal_data = self._journal.update(
                            journal_data,
                            state="UPLOADING",
                            uploaded_bytes=byte_range.last_byte + 1,
                        )
            except ProviderCallError as exc:
                transfer_ambiguous = exc.ambiguous
                if not exc.ambiguous:
                    self._journal.update(
                        journal_data,
                        state="FAILED",
                        terminal_classification=exc.classification,
                    )
                    receipt.update(result=exc.classification, unknown_write=False)
                    return validate_redacted_canary_receipt(
                        receipt, secret_values=secrets
                    )
                journal_data = self._journal.update(
                    journal_data,
                    state="UNKNOWN_WRITE",
                    terminal_classification=exc.classification,
                )

            if not transfer_ambiguous:
                journal_data = self._journal.update(
                    journal_data,
                    state="MEDIA_TRANSFERRED",
                    uploaded_bytes=prepared.size_bytes,
                )
            return self._poll_status(
                access_token=security.access_token,
                journal_data=journal_data,
                receipt=receipt,
                transfer_was_ambiguous=transfer_ambiguous,
                secret_values=secrets,
            )
        except CanarySecurePreflightError as exc:
            receipt.update(
                result=exc.classification,
                oauth_refresh_success=exc.oauth_refresh_success,
                identity_preflight_success=exc.identity_preflight_success,
                required_scopes_satisfied=exc.required_scopes_satisfied,
                refresh_token_rotation_persisted=(
                    exc.refresh_token_rotation_persisted
                ),
            )
            return validate_redacted_canary_receipt(
                receipt, secret_values=secrets
            )
        except (TikTokCanaryError, TikTokSecureSessionError, TikTokOAuthError) as exc:
            receipt["result"] = getattr(exc, "classification", "CANARY_FAILED")
            return validate_redacted_canary_receipt(
                receipt, secret_values=secrets
            )

    def _poll_status(
        self,
        *,
        access_token: str,
        journal_data: dict[str, Any],
        receipt: dict[str, Any],
        transfer_was_ambiguous: bool,
        secret_values: Sequence[str],
    ) -> dict[str, Any]:
        publish_id = str(journal_data.get("publish_id") or "")
        if not publish_id:
            raise TikTokCanaryError("READBACK_PUBLISH_ID_MISSING")
        receipt["publish_id_present"] = True
        for delay in self._poll_schedule_seconds:
            if delay > 0:
                self._sleeper(delay)
            try:
                receipt["status_readback_calls"] += 1
                status_data = self._transport.fetch_status(
                    access_token=access_token,
                    publish_id=publish_id,
                )
            except ProviderCallError as exc:
                self._journal.update(
                    journal_data,
                    state="UNKNOWN_WRITE",
                    terminal_classification=exc.classification,
                )
                receipt.update(result=exc.classification, unknown_write=True)
                return validate_redacted_canary_receipt(
                    receipt, secret_values=secret_values
                )

            raw_status = str(status_data.get("status") or "")
            allowed_statuses = {
                "PROCESSING_UPLOAD",
                "SEND_TO_USER_INBOX",
                "FAILED",
                "PUBLISH_COMPLETE",
            }
            status = (
                raw_status
                if raw_status in allowed_statuses
                else "UNEXPECTED_PROVIDER_STATUS_VALUE"
            )
            uploaded = status_data.get("uploaded_bytes")
            safe_uploaded = int(uploaded) if isinstance(uploaded, int) else None
            receipt["terminal_provider_status"] = status or None
            journal_data = self._journal.update(
                journal_data,
                state=("PROCESSING" if status == "PROCESSING_UPLOAD" else journal_data["state"]),
                last_provider_status=status or None,
                uploaded_bytes=(
                    safe_uploaded
                    if safe_uploaded is not None
                    else journal_data.get("uploaded_bytes", 0)
                ),
            )
            if status == "PROCESSING_UPLOAD":
                continue
            if status == "SEND_TO_USER_INBOX":
                self._journal.update(
                    journal_data,
                    state="DRAFT_DELIVERY_CONFIRMED",
                    terminal_classification="DRAFT_DELIVERY_CONFIRMED",
                )
                receipt.update(
                    result="DRAFT_DELIVERY_CONFIRMED",
                    draft_delivery_confirmed=True,
                    creator_finalization_observed=False,
                    public_post_confirmed=False,
                    unknown_write=False,
                )
                return validate_redacted_canary_receipt(
                    receipt, secret_values=secret_values
                )
            if status == "FAILED":
                self._journal.update(
                    journal_data,
                    state="FAILED",
                    terminal_classification="PROVIDER_REPORTED_FAILED",
                )
                receipt.update(result="PROVIDER_REPORTED_FAILED", unknown_write=False)
                return validate_redacted_canary_receipt(
                    receipt, secret_values=secret_values
                )
            if status == "PUBLISH_COMPLETE":
                public_post_ids = status_data.get("publicaly_available_post_id")
                public_post_confirmed = (
                    isinstance(public_post_ids, Sequence)
                    and not isinstance(public_post_ids, (str, bytes, bytearray))
                    and any(
                        isinstance(post_id, int)
                        and not isinstance(post_id, bool)
                        and post_id > 0
                        for post_id in public_post_ids
                    )
                )
                self._journal.update(
                    journal_data,
                    state="FAILED",
                    terminal_classification="UNEXPECTED_PUBLISH_COMPLETE",
                )
                receipt.update(
                    result="UNEXPECTED_PUBLISH_COMPLETE",
                    creator_finalization_observed=True,
                    public_post_confirmed=public_post_confirmed,
                    unknown_write=False,
                )
                return validate_redacted_canary_receipt(
                    receipt, secret_values=secret_values
                )
            self._journal.update(
                journal_data,
                state="UNKNOWN_WRITE",
                terminal_classification="UNEXPECTED_PROVIDER_STATUS",
            )
            receipt.update(result="UNEXPECTED_PROVIDER_STATUS", unknown_write=True)
            return validate_redacted_canary_receipt(
                receipt, secret_values=secret_values
            )

        result = (
            "UNRESOLVED_AMBIGUOUS_TRANSFER"
            if transfer_was_ambiguous
            else "STATUS_POLLING_TIMEOUT_NO_REUPLOAD"
        )
        self._journal.update(
            journal_data,
            state="UNKNOWN_WRITE",
            terminal_classification=result,
        )
        receipt.update(result=result, unknown_write=True)
        return validate_redacted_canary_receipt(
            receipt, secret_values=secret_values
        )


def nonsecret_readiness_summary(
    resolver: AcceptedShortPackageResolver,
    *,
    probe: Callable[[Path], Mapping[str, Any]] = ffprobe_media,
) -> dict[str, Any]:
    """Resolve and validate accepted media without credentials or network."""

    authority = resolver.describe_authority()
    media = resolver.validate_media(authority, probe=probe)
    attempt_id = deterministic_canary_attempt_id(
        package_id=authority.package_id,
        media_sha256=authority.media_sha256,
    )
    return {
        "result": "ACCEPTED_SHORT_MEDIA_READY",
        "attempt_id": attempt_id,
        "destination_alias": DESTINATION_ALIAS,
        "delivery_intent": DELIVERY_INTENT,
        "provider_intent_version": PROVIDER_INTENT_VERSION,
        "media": media.nonsecret_metadata(),
        "real_credential_reads": 0,
        "real_env_secret_reads": 0,
        "real_oauth_refresh_calls": 0,
        "real_user_info_calls": 0,
        "real_content_posting_init_calls": 0,
        "real_upload_transfers": 0,
        "real_status_calls": 0,
        "real_draft_deliveries": 0,
        "public_writes": 0,
        "v1_mutations": 0,
        "scheduler_mutations": 0,
        "remotion_renders": 0,
    }
