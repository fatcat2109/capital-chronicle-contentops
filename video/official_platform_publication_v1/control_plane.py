"""State and authority boundary for official-platform publication attempts."""

from __future__ import annotations

from typing import Any, Mapping

from .models import (
    DestinationBinding,
    PublicationAttempt,
    PublicationContractError,
    PublicationState,
    ReconciliationResult,
    deterministic_attempt_id,
)
from .providers.base import OfficialProviderAdapter


ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY = True
LIVE_PROVIDER_WRITE_AUTHORITY = False


class WriteAuthorityError(PermissionError):
    """A provider mutation was requested without exact owner authority."""


class UnknownWriteRetryError(RuntimeError):
    """Blind retry was attempted while provider acceptance is unresolved."""


_TRANSITIONS: dict[PublicationState, set[PublicationState]] = {
    PublicationState.PREPARED: {PublicationState.WRITE_AUTHORITY_REQUIRED, PublicationState.FAILED},
    PublicationState.WRITE_AUTHORITY_REQUIRED: {
        PublicationState.INITIATED,
        PublicationState.UNKNOWN_WRITE,
        PublicationState.FAILED,
    },
    PublicationState.INITIATED: {
        PublicationState.MEDIA_TRANSFERRED,
        PublicationState.PROCESSING,
        PublicationState.UNKNOWN_WRITE,
        PublicationState.FAILED,
    },
    PublicationState.MEDIA_TRANSFERRED: {
        PublicationState.PROCESSING,
        PublicationState.PUBLISHED_UNCONFIRMED,
        PublicationState.UNKNOWN_WRITE,
        PublicationState.FAILED,
    },
    PublicationState.PROCESSING: {
        PublicationState.DRAFT_DELIVERED_TO_CREATOR,
        PublicationState.PUBLISHED_UNCONFIRMED,
        PublicationState.READBACK_CONFIRMED,
        PublicationState.UNKNOWN_WRITE,
        PublicationState.FAILED,
    },
    PublicationState.PUBLISHED_UNCONFIRMED: {
        PublicationState.READBACK_CONFIRMED,
        PublicationState.UNKNOWN_WRITE,
        PublicationState.FAILED,
    },
    PublicationState.DRAFT_DELIVERED_TO_CREATOR: {
        PublicationState.READBACK_CONFIRMED,
        PublicationState.UNKNOWN_WRITE,
        PublicationState.FAILED,
    },
    PublicationState.UNKNOWN_WRITE: {
        PublicationState.READBACK_CONFIRMED,
        PublicationState.FAILED,
    },
    PublicationState.READBACK_CONFIRMED: set(),
    PublicationState.FAILED: set(),
}


class WriteAuthorityGate:
    """Compile-time false live-write gate; environment values cannot enable it."""

    @staticmethod
    def require_for_real_provider_mutation() -> None:
        if ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY or not LIVE_PROVIDER_WRITE_AUTHORITY:
            raise WriteAuthorityError(
                "ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY: a later exact owner task is required"
            )


class PublicationControlPlane:
    def __init__(self, adapters: Mapping[Any, OfficialProviderAdapter]) -> None:
        self._adapters = dict(adapters)

    def prepare(
        self,
        package: Mapping[str, Any],
        binding: DestinationBinding,
    ) -> PublicationAttempt:
        if package.get("package_id") != binding.package_id:
            raise PublicationContractError("Destination package_id does not match the package")
        if package.get("language") != binding.destination_locale:
            raise PublicationContractError(
                "Destination locale must exactly select the package language"
            )
        adapter = self._adapters[binding.surface]
        adapter.validate_package(package, binding.surface)
        adapter.validate_destination(binding)
        attempt_id = deterministic_attempt_id(binding)
        plan = adapter.prepare(package, binding, attempt_id)
        attempt = PublicationAttempt(
            attempt_id=attempt_id,
            binding=binding,
            package=package,
            plan=plan,
        )
        attempt.record("PACKAGE_AND_DESTINATION_PREPARED")
        self.transition(attempt, PublicationState.WRITE_AUTHORITY_REQUIRED, "LIVE_WRITE_GATE_BLOCKED")
        return attempt

    @staticmethod
    def transition(
        attempt: PublicationAttempt,
        state: PublicationState,
        event: str,
        **details: Any,
    ) -> None:
        if state not in _TRANSITIONS[attempt.state]:
            raise PublicationContractError(
                f"Illegal publication transition: {attempt.state.value} -> {state.value}"
            )
        attempt.state = state
        attempt.record(event, **details)

    @staticmethod
    def assert_retry_allowed(attempt: PublicationAttempt) -> None:
        if attempt.state is PublicationState.UNKNOWN_WRITE:
            raise UnknownWriteRetryError(
                "STOP RETRY -> READ BACK -> RECONCILE: provider acceptance is unknown"
            )

    @staticmethod
    def block_real_provider_mutation(attempt: PublicationAttempt) -> None:
        attempt.record("REAL_PROVIDER_MUTATION_REFUSED")
        WriteAuthorityGate.require_for_real_provider_mutation()

    def reconcile(
        self,
        attempt: PublicationAttempt,
        readback: Mapping[str, Any],
    ) -> ReconciliationResult:
        adapter = self._adapters[attempt.binding.surface]
        result = adapter.reconcile(attempt, readback)
        attempt.reconciliation = result
        if result.matched:
            self.transition(
                attempt,
                PublicationState.READBACK_CONFIRMED,
                "PROVIDER_OBJECT_READBACK_RECONCILED",
                provider_object_id=result.provider_object_id,
            )
        else:
            attempt.record(
                "READBACK_DID_NOT_ESTABLISH_PROVIDER_OBJECT",
                unresolved=list(result.unresolved),
            )
        return result
