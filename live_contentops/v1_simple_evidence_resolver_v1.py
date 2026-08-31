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
from live_contentops.v1_simple_epistemic_state_v1 import (
    build_epistemic_state,
    canonical_x_report_document,
)

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
        source_route_health: Mapping[str, Any] | None = None,
    ) -> None:
        if int(max_requests) != 6:
            raise ValueError("simple_evidence_global_request_limit_must_equal_six")
        self._evaluation_as_of_utc = str(evaluation_as_of_utc)
        self._max_requests = int(max_requests)
        self._timeout_seconds = float(timeout_seconds)
        self._http_get = http_get
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._shared_request_budget = {"limit": self._max_requests, "used": 0}
        self._source_route_health = SourceRouteHealthState(
            source_route_health, clock=self._clock
        )
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
            "attributed_publisher_identity": provenance.get(
                "attributed_publisher_identity"
            ),
            "rss_candidate_publisher_identities_observed": list(
                provenance.get("rss_candidate_publisher_identities_observed")
                or []
            ),
            "publisher_identities_eligible_for_resolution": list(
                provenance.get("publisher_identities_eligible_for_resolution")
                or []
            ),
            "publisher_resolution_attempted_identities": list(
                provenance.get("publisher_resolution_attempted_identities") or []
            ),
            "attributed_publisher_pinning_applied": bool(
                provenance.get("attributed_publisher_pinning_applied")
            ),
            "publisher_pinning_grants_report_or_event_authority": False,
        }

    def _normalized_result(
        self,
        *,
        request: Mapping[str, Any],
        result: Mapping[str, Any],
        route_history: list[dict[str, Any]],
        call_start: int,
        selected_route: str | None,
        epistemic_state: Mapping[str, Any] | None = None,
        accepted_documents: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        raw_documents = (
            result.get("official_source_documents")
            if selected_route == "OFFICIAL_PRIMARY"
            else result.get("evidence_documents")
        ) or []
        documents = accepted_documents if accepted_documents is not None else [
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
            "epistemic_state": dict(epistemic_state or {}),
            "publication_authority": False,
        }

    @staticmethod
    def _accepted_epistemic_route(
        request: Mapping[str, Any],
        result: Mapping[str, Any],
        *,
        route: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None, list[str]]:
        raw_documents = (
            result.get("official_source_documents")
            if route == "OFFICIAL_PRIMARY"
            else result.get("evidence_documents")
        ) or []
        documents = [
            dict(row)
            for row in raw_documents
            if isinstance(row, Mapping) and row.get("public_claim_allowed") is True
        ]
        context = request.get("story_context")
        context = context if isinstance(context, Mapping) else {}
        if "report_provenance" not in context:
            return documents, {}, []
        state, blockers = build_epistemic_state(
            request=request,
            documents=documents,
            selected_route=route,
        )
        if state is None:
            return [], None, blockers
        accepted_ids = set(state.get("supporting_document_ids") or [])
        accepted = [
            row for row in documents if str(row.get("document_id") or "") in accepted_ids
        ]
        return accepted, state, []

    def __call__(self, request: Mapping[str, Any]) -> dict[str, Any]:
        call_start = self.request_count
        route_history: list[dict[str, Any]] = []
        last_result: Mapping[str, Any] = {}

        context = request.get("story_context")
        context = context if isinstance(context, Mapping) else {}
        report_profile = context.get("report_provenance")
        report_profile = report_profile if isinstance(report_profile, Mapping) else {}
        direct_named_publisher_bound = bool(
            report_profile.get("explicit_reputable_attribution") is True
            and _has_bound_reputable_secondary(request)
        )
        relay_document, _canonical_x_blockers = (
            (None, ["canonical_x_direct_named_publisher_route_preferred"])
            if direct_named_publisher_bound
            else canonical_x_report_document(request)
        )
        if relay_document is not None:
            relay_route = (
                "TRUSTED_RELAY_ATTRIBUTED_REPORT"
                if report_profile.get("explicit_reputable_attribution") is True
                else "TRUSTED_MARKET_RUMOR"
            )
            last_result = {
                "status": "PASS",
                "evidence_documents": [relay_document],
                "provided_evidence_capabilities": ["attributed_report_provenance"],
                "blockers": [],
                "provenance": {"request_count": 0},
            }
            accepted, state, state_blockers = self._accepted_epistemic_route(
                request,
                last_result,
                route=relay_route,
            )
            route_history.append(
                {
                    "route": relay_route,
                    "status": "PASS" if accepted else "BLOCKED",
                    "request_count_for_route": 0,
                    "request_count_total_after_route": self.request_count,
                    "accepted_document_count": len(accepted),
                    "blockers": state_blockers,
                    "locator_surface_id": "exact_governed_canonical_x_sidecar",
                    "locator_bytes_grant_factual_authority": False,
                }
            )
            if accepted and state is not None:
                return self._normalized_result(
                    request=request,
                    result=last_result,
                    route_history=route_history,
                    call_start=call_start,
                    selected_route=relay_route,
                    epistemic_state=state,
                    accepted_documents=accepted,
                )
            return self._normalized_result(
                request=request,
                result=last_result,
                route_history=route_history,
                call_start=call_start,
                selected_route=None,
                accepted_documents=[],
            )

        attributed_report_first = bool(
            report_profile.get("explicit_reputable_attribution") is True
        )

        def try_secondary() -> dict[str, Any] | None:
            nonlocal last_result
            allowance = self._secondary_allowance(call_start=call_start)
            if allowance <= 0:
                return None
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
            route_row = self._route_row(
                "REPUTABLE_SECONDARY",
                last_result,
                before=before,
                after=self.request_count,
            )
            accepted, state, state_blockers = self._accepted_epistemic_route(
                request,
                last_result,
                route="REPUTABLE_SECONDARY",
            )
            if state_blockers:
                route_row["blockers"] = sorted(
                    set(route_row.get("blockers") or []).union(state_blockers)
                )
                route_row["status"] = "BLOCKED"
                route_row["accepted_document_count"] = 0
            route_history.append(route_row)
            if accepted and state is not None:
                return self._normalized_result(
                    request=request,
                    result=last_result,
                    route_history=route_history,
                    call_start=call_start,
                    selected_route="REPUTABLE_SECONDARY",
                    epistemic_state=state,
                    accepted_documents=accepted,
                )
            return None

        # For an explicitly attributed reputable report, prove report truth first and do not
        # spend the bounded ledger hunting for generic issuer confirmation.
        if attributed_report_first:
            resolved = try_secondary()
            if resolved is not None:
                return resolved
            return self._normalized_result(
                request=request,
                result=last_result,
                route_history=route_history,
                call_start=call_start,
                selected_route=None,
                accepted_documents=[],
            )

        # Otherwise retain the shortest governed route, but require exact selected-event support;
        # a same-entity/different-event official document never qualifies the candidate.
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
            accepted, state, state_blockers = self._accepted_epistemic_route(
                request,
                last_result,
                route="OFFICIAL_PRIMARY",
            )
            if state_blockers:
                route_history[-1]["blockers"] = sorted(
                    set(route_history[-1].get("blockers") or []).union(state_blockers)
                )
                route_history[-1]["status"] = "BLOCKED"
                route_history[-1]["accepted_document_count"] = 0
            if accepted and state is not None:
                return self._normalized_result(
                    request=request,
                    result=last_result,
                    route_history=route_history,
                    call_start=call_start,
                    selected_route="OFFICIAL_PRIMARY",
                    epistemic_state=state,
                    accepted_documents=accepted,
                )

        resolved = try_secondary()
        if resolved is not None:
            return resolved

        return self._normalized_result(
            request=request,
            result=last_result,
            route_history=route_history,
            call_start=call_start,
            selected_route=None,
            accepted_documents=[],
        )

    def source_route_health_snapshot(self) -> dict[str, Any]:
        return self._source_route_health.snapshot()
