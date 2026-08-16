"""Durable non-secret contracts for V2 platform publication attempts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class PublicationContractError(RuntimeError):
    """A fail-closed publication-contract violation."""


class Platform(str, Enum):
    YOUTUBE = "YOUTUBE"
    TIKTOK = "TIKTOK"
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"


class Surface(str, Enum):
    YOUTUBE_NORMAL_VIDEO = "YOUTUBE_NORMAL_VIDEO"
    YOUTUBE_SHORTS = "YOUTUBE_SHORTS"
    TIKTOK = "TIKTOK"
    INSTAGRAM_REELS = "INSTAGRAM_REELS"
    INSTAGRAM_STORIES = "INSTAGRAM_STORIES"
    FACEBOOK_REELS = "FACEBOOK_REELS"


class AdapterCapabilityState(str, Enum):
    READY_FOR_FUTURE_LIVE_CANARY = "READY_FOR_FUTURE_LIVE_CANARY"
    ACCOUNT_SETUP_REQUIRED = "ACCOUNT_SETUP_REQUIRED"
    APP_REVIEW_REQUIRED = "APP_REVIEW_REQUIRED"
    INTERACTIVE_CONSENT_REQUIRED = "INTERACTIVE_CONSENT_REQUIRED"
    PRODUCT_POLICY_BLOCKED = "PRODUCT_POLICY_BLOCKED"
    UNRESOLVED = "UNRESOLVED"


class PublicationState(str, Enum):
    PREPARED = "PREPARED"
    WRITE_AUTHORITY_REQUIRED = "WRITE_AUTHORITY_REQUIRED"
    INITIATED = "INITIATED"
    MEDIA_TRANSFERRED = "MEDIA_TRANSFERRED"
    PROCESSING = "PROCESSING"
    PUBLISHED_UNCONFIRMED = "PUBLISHED_UNCONFIRMED"
    READBACK_CONFIRMED = "READBACK_CONFIRMED"
    FAILED = "FAILED"
    UNKNOWN_WRITE = "UNKNOWN_WRITE"


SURFACE_PLATFORM: dict[Surface, Platform] = {
    Surface.YOUTUBE_NORMAL_VIDEO: Platform.YOUTUBE,
    Surface.YOUTUBE_SHORTS: Platform.YOUTUBE,
    Surface.TIKTOK: Platform.TIKTOK,
    Surface.INSTAGRAM_REELS: Platform.INSTAGRAM,
    Surface.INSTAGRAM_STORIES: Platform.INSTAGRAM,
    Surface.FACEBOOK_REELS: Platform.FACEBOOK,
}

SURFACE_FORMAT: dict[Surface, str] = {
    Surface.YOUTUBE_NORMAL_VIDEO: "LONGFORM_16_9",
    Surface.YOUTUBE_SHORTS: "SHORT_9_16",
    Surface.TIKTOK: "SHORT_9_16",
    Surface.INSTAGRAM_REELS: "SHORT_9_16",
    Surface.INSTAGRAM_STORIES: "SHORT_9_16",
    Surface.FACEBOOK_REELS: "SHORT_9_16",
}

_SECRET_KEY_PARTS = (
    "token",
    "auth_header",
    "authorization",
    "secret",
    "credential",
    "cookie",
    "password",
    "session",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _walk_items(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk_items(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _walk_items(item)


def assert_no_secret_serialization(value: Any) -> None:
    forbidden = [
        key
        for key, _ in _walk_items(value)
        if any(part in key.casefold() for part in _SECRET_KEY_PARTS)
    ]
    if forbidden:
        raise PublicationContractError(
            f"Secret-bearing keys are forbidden in publication artifacts: {sorted(set(forbidden))}"
        )


@dataclass(frozen=True)
class DestinationBinding:
    platform: Platform
    surface: Surface
    destination_identity_kind: str
    expected_identity_id: str
    expected_public_handle: str
    destination_locale: str
    package_id: str
    desired_publication_mode: str
    adapter_capability_state: AdapterCapabilityState
    publication_intent_version: str = "v1"

    def __post_init__(self) -> None:
        if SURFACE_PLATFORM[self.surface] is not self.platform:
            raise PublicationContractError("Surface does not belong to the declared platform")
        for label, value in (
            ("destination_identity_kind", self.destination_identity_kind),
            ("expected_identity_id", self.expected_identity_id),
            ("expected_public_handle", self.expected_public_handle),
            ("destination_locale", self.destination_locale),
            ("package_id", self.package_id),
            ("desired_publication_mode", self.desired_publication_mode),
            ("publication_intent_version", self.publication_intent_version),
        ):
            if not value.strip():
                raise PublicationContractError(f"Destination binding requires {label}")
        if not self.package_id.startswith("pkg_"):
            raise PublicationContractError("Destination package_id must be content-addressed")
        if self.desired_publication_mode not in {"PUBLIC", "PRIVATE", "UNLISTED"}:
            raise PublicationContractError("Unsupported desired publication mode")
        assert_no_secret_serialization(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform.value,
            "surface": self.surface.value,
            "destination_identity_kind": self.destination_identity_kind,
            "expected_identity_id": self.expected_identity_id,
            "expected_public_handle": self.expected_public_handle,
            "destination_locale": self.destination_locale,
            "package_id": self.package_id,
            "desired_publication_mode": self.desired_publication_mode,
            "adapter_capability_state": self.adapter_capability_state.value,
            "publication_intent_version": self.publication_intent_version,
        }


def deterministic_attempt_id(binding: DestinationBinding) -> str:
    payload = {
        "schema": "contentops.v2.publication_attempt_identity.v1",
        "package_id": binding.package_id,
        "destination": binding.to_dict(),
        "publication_intent_version": binding.publication_intent_version,
    }
    return f"pubatt_{hashlib.sha256(canonical_json(payload)).hexdigest()}"


@dataclass(frozen=True)
class ProviderRequest:
    operation: str
    method: str
    endpoint: str
    mutation: bool
    body: Mapping[str, Any] | None = None
    query: Mapping[str, Any] | None = None
    headers: Mapping[str, Any] | None = None
    media_artifact: str | None = None
    official_contract: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        assert_no_secret_serialization(value)
        return value


@dataclass(frozen=True)
class ProviderPlan:
    provider: Platform
    surface: Surface
    attempt_id: str
    package_id: str
    destination_locale: str
    requests: tuple[ProviderRequest, ...]
    capability_notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = {
            "provider": self.provider.value,
            "surface": self.surface.value,
            "attempt_id": self.attempt_id,
            "package_id": self.package_id,
            "destination_locale": self.destination_locale,
            "requests": [request.to_dict() for request in self.requests],
            "capability_notes": list(self.capability_notes),
        }
        assert_no_secret_serialization(value)
        return value


@dataclass(frozen=True)
class ReconciliationResult:
    matched: bool
    provider_object_id: str | None
    checks: Mapping[str, bool | str]
    unresolved: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PublicationAttempt:
    attempt_id: str
    binding: DestinationBinding
    package: Mapping[str, Any]
    plan: ProviderPlan
    state: PublicationState = PublicationState.PREPARED
    provider_refs: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    reconciliation: ReconciliationResult | None = None

    def record(self, event: str, **details: Any) -> None:
        assert_no_secret_serialization(details)
        self.history.append(
            {
                "sequence": len(self.history) + 1,
                "event": event,
                "state": self.state.value,
                "details": details,
            }
        )

    def to_receipt(self) -> dict[str, Any]:
        value = {
            "schema": "contentops.v2.canonical_publication_receipt.v1",
            "attempt_id": self.attempt_id,
            "package_id": self.binding.package_id,
            "destination": self.binding.to_dict(),
            "state": self.state.value,
            "provider_refs": dict(self.provider_refs),
            "request_plan": self.plan.to_dict(),
            "history": list(self.history),
            "reconciliation": self.reconciliation.to_dict() if self.reconciliation else None,
            "write_authority": False,
            "real_provider_writes": 0,
        }
        assert_no_secret_serialization(value)
        return value


def load_publication_package(path: Path) -> dict[str, Any]:
    package = json.loads(path.read_text(encoding="utf-8"))
    if package.get("schema") != "contentops.v2.platform_neutral_publication_package.v1":
        raise PublicationContractError("Unsupported platform-neutral package schema")
    if not str(package.get("package_id", "")).startswith("pkg_"):
        raise PublicationContractError("Package has no content-addressed identity")
    boundaries = package.get("hard_boundaries", {})
    if boundaries.get("video_public_write_authority") is not False:
        raise PublicationContractError("ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY is required")
    if boundaries.get("v1_mutation_authority") is not False:
        raise PublicationContractError("V1 mutation authority must be false")
    if boundaries.get("scheduler_mutation_authority") is not False:
        raise PublicationContractError("Scheduler mutation authority must be false")
    artifacts = package.get("artifacts", {})
    media = artifacts.get("clean_video") or artifacts.get("canonical_picture")
    if not isinstance(media, Mapping) or not media.get("path") or not media.get("sha256"):
        raise PublicationContractError("Package has no canonical clean media identity")
    for name in ("caption_srt", "caption_vtt", "audio"):
        artifact = artifacts.get(name)
        if not isinstance(artifact, Mapping) or not artifact.get("path") or not artifact.get("sha256"):
            raise PublicationContractError(f"Package artifact is incomplete: {name}")
    metadata = package.get("metadata", {})
    if not str(metadata.get("title", "")).strip() or not str(metadata.get("description", "")).strip():
        raise PublicationContractError("Package metadata requires title and description")
    assert_no_secret_serialization(package)
    return package


def media_artifact(package: Mapping[str, Any]) -> Mapping[str, Any]:
    artifacts = package["artifacts"]
    return artifacts.get("clean_video") or artifacts["canonical_picture"]
