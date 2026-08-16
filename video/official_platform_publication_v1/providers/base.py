"""Common interface without flattening provider-specific semantics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from ..models import (
    DestinationBinding,
    ProviderPlan,
    PublicationAttempt,
    PublicationContractError,
    ReconciliationResult,
    SURFACE_FORMAT,
    Surface,
    media_artifact,
)


class OfficialProviderAdapter(ABC):
    supported_surfaces: frozenset[Surface]

    def validate_package(self, package: Mapping[str, Any], surface: Surface) -> None:
        if surface not in self.supported_surfaces:
            raise PublicationContractError(f"Adapter does not support {surface.value}")
        if package.get("format") != SURFACE_FORMAT[surface]:
            raise PublicationContractError(
                f"{surface.value} requires {SURFACE_FORMAT[surface]}, got {package.get('format')}"
            )
        if package.get("hard_boundaries", {}).get("video_public_write_authority") is not False:
            raise PublicationContractError("Package must preserve zero video public-write authority")
        media = media_artifact(package)
        if not str(media.get("path", "")).strip() or not str(media.get("sha256", "")).strip():
            raise PublicationContractError("Canonical media artifact identity is incomplete")

    def validate_destination(self, binding: DestinationBinding) -> None:
        if binding.surface not in self.supported_surfaces:
            raise PublicationContractError("Destination surface is unsupported by this adapter")

    @abstractmethod
    def identity_readiness(self, binding: DestinationBinding) -> Mapping[str, Any]:
        """Return non-secret requirements and eligibility truth."""

    @abstractmethod
    def prepare(
        self,
        package: Mapping[str, Any],
        binding: DestinationBinding,
        attempt_id: str,
    ) -> ProviderPlan:
        """Build, but never execute, the official provider request plan."""

    @abstractmethod
    def reconcile(
        self,
        attempt: PublicationAttempt,
        readback: Mapping[str, Any],
    ) -> ReconciliationResult:
        """Match provider readback to the intended package and destination."""


def metadata(package: Mapping[str, Any]) -> Mapping[str, Any]:
    return package["metadata"]
