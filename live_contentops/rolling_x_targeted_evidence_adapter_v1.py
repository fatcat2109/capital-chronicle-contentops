"""Targeted governed evidence receipts for ranked rolling-X stories."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit

from live_contentops.cc_evidence_bridge_v2 import (
    build_evidence_packet_from_cc_root,
    validate_evidence_packet,
)
from live_contentops.freshness_market_state_v2 import evaluate_freshness
from live_contentops.claim_evidence_contract_v1 import build_claim_evidence_contract
from live_contentops.source_capability_registry_v2 import (
    load_source_capability_registry,
    resolve_story_capabilities,
)

PUBLICATION_AUTHORIZED = "PASS_PUBLICATION_AUTHORIZED"
MARKET_CAPABILITIES = frozenset({"current_market_snapshot", "prior_close"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _exact_bound_official_families(
    request: Mapping[str, Any],
    official_hosts_by_family: Mapping[str, Any],
) -> set[str]:
    """Authorize optional official acquisition only from exact headline-bound allowlisted hosts."""
    context = request.get("story_context")
    context = context if isinstance(context, Mapping) else {}
    headline_ids = {str(value) for value in (request.get("headline_ids") or [])}
    hosts: set[str] = set()
    for row in context.get("official_source_url_bindings") or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("headline_id") or "") not in headline_ids:
            continue
        try:
            parsed = urlsplit(str(row.get("url") or ""))
        except ValueError:
            continue
        if parsed.scheme != "https" or parsed.username or parsed.password:
            continue
        host = str(parsed.hostname or "").casefold()
        if host:
            hosts.add(host)
    return {
        str(family)
        for family, allowed_hosts in official_hosts_by_family.items()
        if hosts.intersection({str(host).casefold() for host in allowed_hosts})
    }


def _blocked_receipt(
    request: Mapping[str, Any],
    blockers: list[str],
    *,
    documents: list[dict[str, Any]] | None = None,
    supplied: list[str] | None = None,
    evidence_acquisition_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": "BLOCKED",
        "cluster_id": request.get("cluster_id"),
        "headline_ids": list(request.get("headline_ids") or []),
        "provided_evidence_capabilities": sorted(set(supplied or [])),
        "evidence_documents": list(documents or []),
        "capital_chronicle_authority_verified": False,
        "numeric_evidence_required": bool(
            request.get(
                "capital_chronicle_numeric_or_analytical_authority_required"
            )
        ),
        "blockers": sorted(set(blockers)),
        "publication_authority": False,
        "evidence_acquisition_provenance": dict(evidence_acquisition_provenance or {}),
    }


def _exact_binding_blockers(
    packet: Mapping[str, Any], request: Mapping[str, Any]
) -> list[str]:
    binding = packet.get("rolling_x_story_binding")
    if not isinstance(binding, Mapping):
        return ["governed_rolling_x_story_binding_missing"]
    blockers = []
    if str(binding.get("cluster_id") or "") != str(request.get("cluster_id") or ""):
        blockers.append("governed_evidence_cluster_binding_mismatch")
    if [str(value) for value in (binding.get("headline_ids") or [])] != [
        str(value) for value in (request.get("headline_ids") or [])
    ]:
        blockers.append("governed_evidence_headline_binding_mismatch")
    if str(binding.get("request_logical_hash") or "") != str(
        request.get("request_logical_hash") or ""
    ):
        blockers.append("governed_evidence_request_hash_mismatch")
    return blockers


def _document_receipts(
    packet: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    freshness_state: str,
    official_primary_required: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    documents: list[dict[str, Any]] = []
    blockers: list[str] = []
    binding = dict(packet.get("rolling_x_story_binding") or {})
    provenance = dict(packet.get("provenance") or {})
    packet_hash = (
        packet.get("logical_hash")
        or packet.get("content_sha256")
        or (packet.get("governed_contract") or {}).get("upstream_packet_sha256")
        or (provenance.get("publication_packet") or {}).get("sha256")
    )
    known_at = (
        provenance.get("retrieved_at_utc")
        or packet.get("generated_at_utc")
        or packet.get("as_of_utc")
    )
    for index, raw in enumerate(packet.get("official_source_documents") or []):
        if not isinstance(raw, Mapping):
            continue
        row = dict(raw)
        source_url = row.get("source_url") or row.get("data_url")
        source_identity = row.get("publisher") or row.get("source_id")
        authority_class = row.get("source_authority_class") or row.get(
            "authority_class"
        )
        content_hash = (
            row.get("raw_sha256")
            or row.get("content_sha256")
            or row.get("canonical_content_sha256")
            or packet_hash
        )
        missing = []
        if not source_url:
            missing.append("source_url")
        if not source_identity:
            missing.append("source_identity")
        if not authority_class:
            missing.append("source_authority_class")
        elif official_primary_required and (
            authority_class != "official_public_primary_source"
        ):
            missing.append("official_primary_source_authority")
        if not known_at:
            missing.append("known_at_utc")
        if not content_hash:
            missing.append("content_sha256")
        if row.get("public_claim_allowed") is not True:
            missing.append("public_claim_permission")
        if missing:
            blockers.extend(
                f"official_evidence_document_{index}_missing:{field}"
                for field in missing
            )
            continue
        documents.append(
            {
                **row,
                "source_url": source_url,
                "source_identity": source_identity,
                "source_authority_class": authority_class,
                "known_at_utc": known_at,
                "content_sha256": content_hash,
                "cluster_id": binding.get("cluster_id"),
                "headline_ids": list(binding.get("headline_ids") or []),
                "request_logical_hash": binding.get("request_logical_hash"),
                "permission_state": "PUBLIC_CLAIM_ALLOWED",
                "freshness_state": freshness_state,
                "source_artifact_ref": row.get("source_artifact_ref")
                or f"packet:{packet.get('packet_id')}#official_source_documents/{index}",
            }
        )
    return documents, blockers


def _market_capabilities(packet: Mapping[str, Any]) -> tuple[set[str], list[str]]:
    supplied: set[str] = set()
    blockers: list[str] = []
    claims = [
        row
        for row in (packet.get("numeric_claims") or [])
        if isinstance(row, Mapping)
        and row.get("public_claim_allowed") is True
        and row.get("llm_numeric_authority") is False
        and row.get("source_artifact_ref")
        and row.get("observation_time_utc")
        and row.get("value") is not None
    ]
    snapshots = [
        row
        for row in (packet.get("market_snapshots") or [])
        if isinstance(row, Mapping)
    ]
    if claims and snapshots:
        supplied.add("current_market_snapshot")
    else:
        blockers.append("governed_current_market_snapshot_missing")
    if any(
        row.get("prior_close") is not None or row.get("prior_value") is not None
        for row in claims
    ):
        supplied.add("prior_close")
    else:
        blockers.append("governed_prior_close_missing")
    return supplied, blockers


def _official_freshness_blockers(
    documents: list[Mapping[str, Any]], *, evaluation_as_of_utc: str, max_age_hours: float
) -> list[str]:
    try:
        cutoff = datetime.fromisoformat(evaluation_as_of_utc.replace("Z", "+00:00"))
    except ValueError:
        return ["official_evidence_evaluation_time_invalid"]
    blockers = []
    for index, row in enumerate(documents):
        value = row.get("published_at_utc") or row.get("event_time_utc")
        try:
            observed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            blockers.append(f"official_evidence_document_{index}_published_time_invalid")
            continue
        age_hours = (cutoff - observed).total_seconds() / 3600.0
        if age_hours < 0 or age_hours > max_age_hours:
            blockers.append(f"official_evidence_document_{index}_stale_or_future")
    return blockers


class RollingXTargetedEvidenceAdapter:
    """Translate exact governed packets into the existing rolling-X receipt contract."""

    def __init__(
        self,
        *,
        capital_chronicle_root: str | Path | None = None,
        evaluation_as_of_utc: str | None = None,
        packet_loader: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        official_evidence_loader: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        public_secondary_loader: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        capability_registry: Mapping[str, Any] | None = None,
    ) -> None:
        self._root = Path(capital_chronicle_root) if capital_chronicle_root else None
        self._evaluation_as_of_utc = evaluation_as_of_utc or _utc_now()
        self._packet_loader = packet_loader
        if official_evidence_loader is None:
            from live_contentops.official_primary_evidence_loader_v1 import (
                BoundedOfficialPrimaryEvidenceLoader,
            )

            official_evidence_loader = BoundedOfficialPrimaryEvidenceLoader(
                evaluation_as_of_utc=self._evaluation_as_of_utc
            )
        self._official_evidence_loader = official_evidence_loader
        if public_secondary_loader is None:
            from live_contentops.public_secondary_evidence_loader_v1 import (
                BoundedPublicSecondaryEvidenceLoader,
            )

            public_secondary_loader = BoundedPublicSecondaryEvidenceLoader(
                evaluation_as_of_utc=self._evaluation_as_of_utc
            )
        self._public_secondary_loader = public_secondary_loader
        self._registry = dict(
            capability_registry or load_source_capability_registry()
        )
        self._packet: dict[str, Any] | None = None
        self._load_error: str | None = None

    def _load_packet(self, request: Mapping[str, Any]) -> dict[str, Any] | None:
        if self._packet_loader is not None:
            try:
                raw = self._packet_loader(request)
            except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
                self._load_error = (
                    "capital_chronicle_evidence_packet_unavailable:"
                    + type(exc).__name__
                )
                return None
            if not isinstance(raw, Mapping):
                self._load_error = "capital_chronicle_evidence_packet_not_object"
                return None
            return dict(raw)
        if self._packet is not None or self._load_error is not None:
            return self._packet
        try:
            if self._root is not None:
                raw = build_evidence_packet_from_cc_root(
                    self._root,
                    as_of_utc=self._evaluation_as_of_utc,
                )
            else:
                self._load_error = "capital_chronicle_evidence_root_not_bound"
                return None
            if not isinstance(raw, Mapping):
                self._load_error = "capital_chronicle_evidence_packet_not_object"
                return None
            self._packet = dict(raw)
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
            self._load_error = (
                "capital_chronicle_evidence_packet_unavailable:"
                + type(exc).__name__
            )
        return self._packet

    def __call__(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if request.get("x_content_is_discovery_and_ranking_only") is not True:
            return _blocked_receipt(
                request, ["x_discovery_only_contract_missing"]
            )
        story_type = str(request.get("story_type") or "")
        configured = (self._registry.get("story_types") or {}).get(story_type) or {}
        capability = resolve_story_capabilities(
            {
                "story_type": story_type,
                "article_mode": str(request.get("article_mode") or ""),
            },
            self._registry,
        )
        blockers = list(capability.get("blockers") or [])
        required = [
            str(value)
            for value in request.get("required_evidence_capabilities") or []
        ]
        if required != list(capability.get("required_evidence_capabilities") or []):
            blockers.append("evidence_request_capability_registry_mismatch")
        families = set(capability.get("source_adapter_families") or [])
        if not families or families != set(
            request.get("source_adapter_families") or families
        ):
            blockers.append("evidence_request_source_adapter_registry_mismatch")
        if blockers:
            return _blocked_receipt(request, blockers)

        families = set(capability.get("source_adapter_families") or [])
        cc_families = {"capital_chronicle_market_state", "capital_chronicle_database"}
        if not families.intersection(cc_families):
            from live_contentops.official_primary_evidence_loader_v1 import (
                OFFICIAL_HOSTS_BY_FAMILY,
                SUPPORTED_FAMILIES,
            )

            documents: list[dict[str, Any]] = []
            supplied: set[str] = set()
            diagnostics: dict[str, Any] = {}
            registry_official_families = families.intersection(SUPPORTED_FAMILIES)
            exact_bound_official_families = _exact_bound_official_families(
                request, OFFICIAL_HOSTS_BY_FAMILY
            )
            official_families = sorted(
                registry_official_families.union(exact_bound_official_families)
            )
            if official_families:
                official_request = {
                    **dict(request),
                    "source_adapter_families": official_families,
                    # Acquisition verifies every capability found in the bytes.  Sufficiency is
                    # applied below against the effective mode, not inside the transport.
                    "required_evidence_capabilities": [],
                }
                try:
                    official_raw = self._official_evidence_loader(official_request)
                    official = dict(official_raw) if isinstance(official_raw, Mapping) else {}
                except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
                    official = {"status": "BLOCKED", "blockers": [
                        "official_source_evidence_unavailable:" + type(exc).__name__
                    ]}
                diagnostics["official"] = {
                    "status": official.get("status"),
                    "blockers": list(official.get("blockers") or []),
                    "provenance": dict(official.get("provenance") or {}),
                    "registry_authorized_families": sorted(registry_official_families),
                    "exact_bound_host_authorized_families": sorted(
                        exact_bound_official_families
                    ),
                }
                if official.get("official_source_documents"):
                    # Rebind the transport packet to the exact effective-mode request.
                    official["rolling_x_story_binding"] = {
                        "cluster_id": request.get("cluster_id"),
                        "headline_ids": list(request.get("headline_ids") or []),
                        "request_logical_hash": request.get("request_logical_hash"),
                    }
                    official_documents, official_document_blockers = _document_receipts(
                        official,
                        request,
                        freshness_state="FRESH_CURRENT_OPERATOR_READINESS",
                        official_primary_required=True,
                    )
                    documents.extend(official_documents)
                    if not official_documents:
                        diagnostics["official"]["document_blockers"] = official_document_blockers
                        blockers.extend(official_document_blockers)
                    supplied.update(
                        str(value)
                        for value in (official.get("provided_evidence_capabilities") or [])
                    )

            if "public_secondary" in families:
                try:
                    secondary_raw = self._public_secondary_loader(request)
                    secondary = dict(secondary_raw) if isinstance(secondary_raw, Mapping) else {}
                except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
                    secondary = {"status": "BLOCKED", "blockers": [
                        "public_secondary_evidence_unavailable:" + type(exc).__name__
                    ]}
                diagnostics["public_secondary"] = {
                    "status": secondary.get("status"),
                    "blockers": list(secondary.get("blockers") or []),
                    "provenance": dict(secondary.get("provenance") or {}),
                }
                binding_blockers = _exact_binding_blockers(secondary, request)
                if not binding_blockers:
                    known_at = (secondary.get("provenance") or {}).get("retrieved_at_utc")
                    for row in secondary.get("evidence_documents") or []:
                        if not isinstance(row, Mapping):
                            continue
                        document = dict(row)
                        if (
                            document.get("source_url")
                            and document.get("source_identity")
                            and document.get("source_authority_class") == "reputable_secondary_source"
                            and document.get("public_claim_allowed") is True
                            and document.get("canonical_content_sha256")
                            and known_at
                        ):
                            document.update(
                                {
                                    "known_at_utc": known_at,
                                    "cluster_id": request.get("cluster_id"),
                                    "headline_ids": list(request.get("headline_ids") or []),
                                    "request_logical_hash": request.get("request_logical_hash"),
                                    "permission_state": "PUBLIC_CLAIM_ALLOWED",
                                    "freshness_state": "FRESH_CURRENT_OPERATOR_READINESS",
                                }
                            )
                            documents.append(document)
                    supplied.update(
                        str(value)
                        for value in (secondary.get("provided_evidence_capabilities") or [])
                    )
                else:
                    diagnostics["public_secondary"]["binding_blockers"] = binding_blockers

            freshness_requirements = capability.get("freshness_requirements") or {}
            fresh_documents: list[dict[str, Any]] = []
            freshness_exclusions: list[dict[str, Any]] = []
            for document in documents:
                findings = _official_freshness_blockers(
                    [document],
                    evaluation_as_of_utc=self._evaluation_as_of_utc,
                    max_age_hours=float(freshness_requirements.get("max_age_hours") or 36.0),
                )
                if findings:
                    freshness_exclusions.append(
                        {
                            "document_id": document.get("document_id"),
                            "findings": findings,
                            "disposition": "EXCLUDED_NOT_A_WHOLE_STORY_VETO",
                        }
                    )
                else:
                    fresh_documents.append(document)
            documents = fresh_documents
            if freshness_exclusions:
                diagnostics["freshness_exclusions"] = freshness_exclusions
                if not documents:
                    blockers.extend(
                        finding
                        for row in freshness_exclusions
                        for finding in row["findings"]
                    )
            claim_contract = build_claim_evidence_contract(request, documents)
            if claim_contract.get("status") == "PASS":
                supplied.update({"credible_event_confirmation", "basic_attributed_facts"})
            else:
                blockers.append("supported_claims_missing")
            if not documents:
                blockers.append("evidence_documents_missing")
            for missing in sorted(set(required) - supplied):
                blockers.append(f"required_evidence_capability_missing:{missing}")
            if blockers:
                receipt = _blocked_receipt(
                    request,
                    blockers,
                    documents=documents,
                    supplied=sorted(supplied),
                    evidence_acquisition_provenance=diagnostics,
                )
                receipt["claim_evidence_contract"] = claim_contract
                return receipt
            return {
                "status": "PASS",
                "cluster_id": request.get("cluster_id"),
                "headline_ids": list(request.get("headline_ids") or []),
                "provided_evidence_capabilities": sorted(supplied),
                "evidence_documents": documents,
                "claim_evidence_contract": claim_contract,
                "unsupported_claims_removed": int(claim_contract.get("omitted_claim_count") or 0),
                "capital_chronicle_authority_verified": False,
                "numeric_evidence_required": False,
                "blockers": [],
                "publication_authority": False,
                "evidence_acquisition_provenance": diagnostics,
            }

        packet = self._load_packet(request)
        if packet is None:
            return _blocked_receipt(
                request,
                [self._load_error or "capital_chronicle_evidence_packet_unavailable"],
            )
        blockers.extend(validate_evidence_packet(packet))
        if packet.get("status") != PUBLICATION_AUTHORIZED:
            blockers.append("governed_packet_not_publication_authorized")
        permissions = packet.get("public_claim_permissions") or {}
        if (
            permissions.get("decision") != "ALLOW"
            or permissions.get("reporting_allowed") is not True
        ):
            blockers.append("governed_reporting_permission_not_granted")
        if permissions.get("llm_numeric_authority") is not False:
            blockers.append("governed_llm_numeric_authority_invalid")
        blockers.extend(_exact_binding_blockers(packet, request))

        freshness_request = {
            "article_mode": capability.get("article_mode"),
            "market_sensitive": bool(capability.get("market_sensitive")),
            "market_snapshot_required": bool(
                capability.get("market_snapshot_required")
            ),
            "fresh_material_delta": bool(
                (packet.get("publication_assignment") or {}).get(
                    "fresh_material_delta"
                )
                or (packet.get("assignment") or {}).get("fresh_material_delta")
            ),
            "readiness_evaluation_basis": "CURRENT_OPERATOR_READINESS",
            "operator_evaluation_as_of_utc": self._evaluation_as_of_utc,
        }
        freshness = evaluate_freshness(packet, freshness_request)
        if freshness.get("decision") != "PASS":
            blockers.extend(freshness.get("blockers") or [])
        freshness_state = (
            "FRESH_CURRENT_OPERATOR_READINESS"
            if freshness.get("decision") == "PASS"
            else "STALE_OR_MISSING"
        )
        documents, document_blockers = _document_receipts(
            packet, request, freshness_state=freshness_state
        )
        blockers.extend(document_blockers)
        claim_contract = build_claim_evidence_contract(request, documents)
        if claim_contract.get("status") != "PASS":
            blockers.append("supported_claims_missing")

        declared_supplied = set(
            str(value)
            for value in packet.get("provided_evidence_capabilities") or []
        )
        supplied = declared_supplied - MARKET_CAPABILITIES - {"catalyst_evidence"}
        market_supplied, market_blockers = _market_capabilities(packet)
        if "capital_chronicle_market_state" in families:
            supplied.update(market_supplied)
            blockers.extend(
                blocker
                for blocker in market_blockers
                if any(capability in required for capability in MARKET_CAPABILITIES)
            )
        elif MARKET_CAPABILITIES.intersection(required):
            blockers.append("capital_chronicle_market_state_adapter_unavailable")
        if "official_catalyst" in families:
            if documents:
                supplied.add("catalyst_evidence")
            elif "catalyst_evidence" in required:
                blockers.append("governed_official_catalyst_evidence_missing")
        supplied.update(
            capability
            for capability in required
            if capability not in MARKET_CAPABILITIES
            and capability != "catalyst_evidence"
            and capability in set(
                packet.get("provided_evidence_capabilities") or []
            )
            and documents
        )
        if claim_contract.get("status") == "PASS":
            supplied.update({"credible_event_confirmation", "basic_attributed_facts"})

        for missing in sorted(set(required) - supplied):
            blockers.append(f"required_evidence_capability_missing:{missing}")
        market_required = bool(
            request.get(
                "capital_chronicle_numeric_or_analytical_authority_required"
            )
        )
        authority_verified = bool(
            market_required
            and not blockers
            and set(required).issubset(supplied)
            and MARKET_CAPABILITIES.intersection(required).issubset(supplied)
        )
        if market_required and not authority_verified:
            blockers.append("capital_chronicle_authority_not_verified")
        if blockers:
            receipt = _blocked_receipt(
                request,
                blockers,
                documents=documents,
                supplied=sorted(supplied.intersection(required)),
            )
            receipt["claim_evidence_contract"] = claim_contract
            return receipt
        return {
            "status": "PASS",
            "cluster_id": request.get("cluster_id"),
            "headline_ids": list(request.get("headline_ids") or []),
            "provided_evidence_capabilities": sorted(
                supplied.intersection(required)
            ),
            "evidence_documents": documents,
            "claim_evidence_contract": claim_contract,
            "unsupported_claims_removed": int(claim_contract.get("omitted_claim_count") or 0),
            "capital_chronicle_authority_verified": authority_verified,
            "numeric_evidence_required": market_required,
            "blockers": [],
            "publication_authority": False,
            "governed_packet_id": packet.get("packet_id"),
            "freshness_decision": freshness,
        }
