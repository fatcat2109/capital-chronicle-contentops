"""First-party-aware deterministic evidence resolver for the Simple V1 lane.

The resolver composes the existing official-primary and reputable-secondary loaders under
one shared request ledger.  It creates no evidence schema or authority: locator bytes remain
discovery-only and only the existing loaders' exact accepted document records can reach the
Simple writer.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit

from live_contentops.official_primary_evidence_loader_v1 import (
    BoundedOfficialPrimaryEvidenceLoader,
    OFFICIAL_HOSTS_BY_FAMILY,
)
from live_contentops.official_primary_source_locator_v1 import (
    routed_official_locator_families,
)
from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
    REPUTABLE_SECONDARY_HOSTS,
)
from live_contentops.source_route_health_v1 import SourceRouteHealthState

SCHEMA_VERSION = "contentops.v1_simple_first_party_aware_evidence_resolver.v1"

_REQUIRED_CAPABILITY_BY_FAMILY = {
    "official_macro": "official_release",
    "official_policy": "official_statement",
    "official_regulatory_fiscal": "official_document",
    "company_primary": "company_filing_or_release",
    "sec_regulatory": "company_filing_or_release",
}


def _bindings(request: Mapping[str, Any]) -> list[dict[str, Any]]:
    context = request.get("story_context") or {}
    return [
        dict(row)
        for row in context.get("public_source_url_bindings") or []
        if isinstance(row, Mapping) and str(row.get("url") or "").startswith("https://")
    ]


def _bound_official_families(request: Mapping[str, Any]) -> tuple[str, ...]:
    hosts = {
        str(urlsplit(str(row.get("url") or "")).hostname or "").casefold()
        for row in _bindings(request)
    }
    return tuple(
        sorted(
            family
            for family, allowed_hosts in OFFICIAL_HOSTS_BY_FAMILY.items()
            if hosts.intersection(allowed_hosts)
        )
    )


def _has_bound_reputable_secondary(request: Mapping[str, Any]) -> bool:
    return any(
        str(urlsplit(str(row.get("url") or "")).hostname or "").casefold()
        in REPUTABLE_SECONDARY_HOSTS
        for row in _bindings(request)
    )


class SimpleFirstPartyAwareEvidenceResolver:
    """Resolve one admitted candidate without exceeding one shared global GET ledger."""

    def __init__(
        self,
        *,
        evaluation_as_of_utc: str,
        max_requests: int = 6,
        timeout_seconds: float = 12.0,
        http_get: Callable[[str, float, int], Mapping[str, Any]] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if int(max_requests) != 6:
            raise ValueError("simple_evidence_global_request_limit_must_equal_six")
        self._evaluation_as_of_utc = str(evaluation_as_of_utc)
        self._max_requests = int(max_requests)
        self._timeout_seconds = float(timeout_seconds)
        self._http_get = http_get
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._shared_request_budget = {"limit": self._max_requests, "used": 0}
        self._source_route_health = SourceRouteHealthState(clock=self._clock)
        self._official_loader = BoundedOfficialPrimaryEvidenceLoader(
            evaluation_as_of_utc=self._evaluation_as_of_utc,
            max_requests=self._max_requests,
            timeout_seconds=self._timeout_seconds,
            http_get=self._http_get,
            clock=self._clock,
            shared_request_budget=self._shared_request_budget,
        )

    @property
    def request_count(self) -> int:
        return int(self._shared_request_budget["used"])

    def _official_family(self, request: Mapping[str, Any]) -> str | None:
        bound = _bound_official_families(request)
        if len(bound) == 1:
            return bound[0]
        routed = tuple(sorted(routed_official_locator_families(request)))
        return routed[0] if len(routed) == 1 else None

    def _official_request(
        self, request: Mapping[str, Any], family: str
    ) -> dict[str, Any]:
        context = dict(request.get("story_context") or {})
        allowed_hosts = OFFICIAL_HOSTS_BY_FAMILY[family]
        official_bindings = [
            row
            for row in _bindings(request)
            if str(urlsplit(str(row.get("url") or "")).hostname or "").casefold()
            in allowed_hosts
        ]
        context["official_source_url_bindings"] = official_bindings
        return {
            **dict(request),
            "source_adapter_families": [family],
            "required_evidence_capabilities": [
                _REQUIRED_CAPABILITY_BY_FAMILY[family]
            ],
            "story_context": context,
        }

    def _secondary_allowance(self, *, call_start: int) -> int:
        remaining_global = self._max_requests - self.request_count
        used_by_active_candidate = self.request_count - call_start
        # The existing reputable-secondary path is normally RSS locator -> publisher
        # sitemap locator -> exact publisher document.  Let the active candidate finish
        # that three-GET path before moving on.  The unchanged shared six-GET ledger
        # therefore admits at most two full completion attempts, without budget growth.
        return max(
            0,
            min(remaining_global, 3 - used_by_active_candidate),
        )

    @staticmethod
    def _route_row(
        route: str,
        result: Mapping[str, Any],
        *,
        before: int,
        after: int,
    ) -> dict[str, Any]:
        documents = (
            result.get("official_source_documents")
            if route == "OFFICIAL_PRIMARY"
            else result.get("evidence_documents")
        ) or []
        provenance = result.get("provenance") or {}
        return {
            "route": route,
            "status": str(result.get("status") or "BLOCKED"),
            "request_count_for_route": after - before,
            "request_count_total_after_route": after,
            "accepted_document_count": sum(
                1
                for row in documents
                if isinstance(row, Mapping) and row.get("public_claim_allowed") is True
            ),
            "blockers": sorted(
                {str(value) for value in result.get("blockers") or [] if str(value)}
            ),
            "locator_surface_id": (
                (provenance.get("locator") or {}).get("locator_surface_id")
                if isinstance(provenance, Mapping)
                else None
            ),
            "locator_bytes_grant_factual_authority": False,
        }

    def _normalized_result(
        self,
        *,
        request: Mapping[str, Any],
        result: Mapping[str, Any],
        route_history: list[dict[str, Any]],
        call_start: int,
        selected_route: str | None,
    ) -> dict[str, Any]:
        raw_documents = (
            result.get("official_source_documents")
            if selected_route == "OFFICIAL_PRIMARY"
            else result.get("evidence_documents")
        ) or []
        documents = [
            dict(row)
            for row in raw_documents
            if isinstance(row, Mapping) and row.get("public_claim_allowed") is True
        ]
        blockers = sorted(
            {
                str(value)
                for route in route_history
                for value in route.get("blockers") or []
                if str(value)
            }
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "PASS" if documents else "BLOCKED",
            "rolling_x_story_binding": {
                "cluster_id": request.get("cluster_id"),
                "headline_ids": list(request.get("headline_ids") or []),
                "request_logical_hash": request.get("request_logical_hash"),
            },
            "evidence_documents": documents,
            "provided_evidence_capabilities": list(
                result.get("provided_evidence_capabilities") or []
            ),
            "provenance": {
                "evaluation_as_of_utc": self._evaluation_as_of_utc,
                "selected_route": selected_route,
                "route_history": route_history,
                "request_count_for_call": self.request_count - call_start,
                "request_count_total": self.request_count,
                "request_limit": self._max_requests,
                "shared_request_budget": True,
                "all_official_and_secondary_gets_share_one_ledger": True,
                "locator_or_search_bytes_are_factual_authority": False,
                "read_only_public_gets": True,
            },
            "blockers": [] if documents else blockers or ["public_source_unavailable"],
            "publication_authority": False,
        }

    def __call__(self, request: Mapping[str, Any]) -> dict[str, Any]:
        call_start = self.request_count
        route_history: list[dict[str, Any]] = []
        last_result: Mapping[str, Any] = {}

        # An exact already-bound reputable source is the shortest trustworthy path.
        # Otherwise, use the deterministic official family route before secondary discovery.
        family = self._official_family(request)
        if family and not _has_bound_reputable_secondary(request):
            before = self.request_count
            last_result = self._official_loader(
                self._official_request(request, family)
            )
            route_history.append(
                self._route_row(
                    "OFFICIAL_PRIMARY",
                    last_result,
                    before=before,
                    after=self.request_count,
                )
            )
            official_documents = [
                row
                for row in last_result.get("official_source_documents") or []
                if isinstance(row, Mapping) and row.get("public_claim_allowed") is True
            ]
            if last_result.get("status") == "PASS" and official_documents:
                return self._normalized_result(
                    request=request,
                    result=last_result,
                    route_history=route_history,
                    call_start=call_start,
                    selected_route="OFFICIAL_PRIMARY",
                )

        allowance = self._secondary_allowance(call_start=call_start)
        if allowance > 0:
            before = self.request_count
            secondary = BoundedPublicSecondaryEvidenceLoader(
                evaluation_as_of_utc=self._evaluation_as_of_utc,
                max_requests=self._max_requests,
                max_requests_per_candidate=allowance,
                timeout_seconds=self._timeout_seconds,
                http_get=self._http_get,
                clock=self._clock,
                source_route_health=self._source_route_health,
                shared_request_budget=self._shared_request_budget,
            )
            last_result = secondary(request)
            route_history.append(
                self._route_row(
                    "REPUTABLE_SECONDARY",
                    last_result,
                    before=before,
                    after=self.request_count,
                )
            )
            secondary_documents = [
                row
                for row in last_result.get("evidence_documents") or []
                if isinstance(row, Mapping) and row.get("public_claim_allowed") is True
            ]
            if last_result.get("status") == "PASS" and secondary_documents:
                return self._normalized_result(
                    request=request,
                    result=last_result,
                    route_history=route_history,
                    call_start=call_start,
                    selected_route="REPUTABLE_SECONDARY",
                )

        return self._normalized_result(
            request=request,
            result=last_result,
            route_history=route_history,
            call_start=call_start,
            selected_route=None,
        )

    def source_route_health_snapshot(self) -> dict[str, Any]:
        return self._source_route_health.snapshot()
