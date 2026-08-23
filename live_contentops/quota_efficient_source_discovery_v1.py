"""Bounded batch/tail invocation economics for the canonical V1 evidence seam.

This module coordinates URL-only discovery.  It does not retrieve evidence, admit claims, mutate
the newsroom/store, invoke an editorial worker, or own publication authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Callable, Mapping

from live_contentops.rolling_x_targeted_evidence_adapter_v1 import (
    validate_codex_source_discovery_batch_contract,
    validate_codex_source_discovery_contract,
)


SCHEMA_VERSION = "contentops.quota_efficient_source_discovery.v1"
DEFAULT_MAX_BATCH_TURNS = 2
DEFAULT_MAX_TAIL_TURNS = 2
DEFAULT_MAX_TOTAL_TURNS = 4
DEFAULT_MAX_ACCOUNTED_TOKENS = 2_000_000
DEFAULT_MAX_DETERMINISTIC_NETWORK_REQUESTS = 96
DEFAULT_MAX_BATCH_STORIES = 12
_DISCOVERY_REQUIRED_MARKERS = frozenset(
    {"SOURCE_DISCOVERY_REQUIRED", "AUTONOMOUS_SOURCE_DISCOVERY_EXHAUSTED"}
)


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _identity(request: Mapping[str, Any]) -> tuple[str, tuple[str, ...]]:
    identity = (
        str(request.get("cluster_id") or ""),
        tuple(sorted(str(value) for value in request.get("headline_ids") or [])),
    )
    if not identity[0] or not identity[1]:
        raise ValueError("quota_discovery_story_identity_invalid")
    return identity


def _identity_row(identity: tuple[str, tuple[str, ...]]) -> dict[str, Any]:
    return {"story_identity": identity[0], "headline_ids": list(identity[1])}


def _network_request_count(receipt: Mapping[str, Any]) -> int:
    provenance = receipt.get("evidence_acquisition_provenance") or {}
    if not isinstance(provenance, Mapping):
        return 0
    official = provenance.get("official") or {}
    official_provenance = (
        official.get("provenance") or {} if isinstance(official, Mapping) else {}
    )
    official_requests = int(
        official_provenance.get("locator_request_count") or 0
    ) + int(official_provenance.get("official_evidence_get_count") or 0)
    grounded = provenance.get("grounded_research") or {}
    public_requests = int(
        grounded.get("public_retrieval_requests") or 0
        if isinstance(grounded, Mapping)
        else 0
    )
    secondary = provenance.get("public_secondary") or {}
    secondary_provenance = (
        secondary.get("provenance") or {}
        if isinstance(secondary, Mapping)
        else {}
    )
    public_requests = max(
        public_requests,
        int(
            secondary_provenance.get("request_count_for_call")
            or secondary_provenance.get("request_count_for_candidate")
            or 0
        ),
    )
    return official_requests + public_requests


class QuotaEfficientSourceDiscoverySession:
    """Cache deterministic receipts and batch only exact unresolved story identities."""

    def __init__(
        self,
        *,
        evidence_acquirer: Callable[[Mapping[str, Any]], Any],
        source_discoverer: Any,
        max_batch_turns: int = DEFAULT_MAX_BATCH_TURNS,
        max_tail_turns: int = DEFAULT_MAX_TAIL_TURNS,
        max_total_turns: int = DEFAULT_MAX_TOTAL_TURNS,
        max_accounted_tokens: int = DEFAULT_MAX_ACCOUNTED_TOKENS,
        max_deterministic_network_requests: int = (
            DEFAULT_MAX_DETERMINISTIC_NETWORK_REQUESTS
        ),
        max_batch_stories: int = DEFAULT_MAX_BATCH_STORIES,
    ) -> None:
        if not callable(evidence_acquirer):
            raise ValueError("quota_discovery_evidence_acquirer_required")
        if not callable(source_discoverer) and not callable(
            getattr(source_discoverer, "discover_batch", None)
        ):
            raise ValueError("quota_discovery_source_discoverer_required")
        if (
            not 1 <= max_batch_turns <= max_total_turns
            or not 1 <= max_tail_turns <= max_total_turns
            or max_total_turns > 4
            or max_accounted_tokens < 1
            or max_accounted_tokens > DEFAULT_MAX_ACCOUNTED_TOKENS
            or max_deterministic_network_requests < 1
            or max_deterministic_network_requests
            > DEFAULT_MAX_DETERMINISTIC_NETWORK_REQUESTS
            or not 1 <= max_batch_stories <= DEFAULT_MAX_BATCH_STORIES
        ):
            raise ValueError("quota_discovery_budget_invalid")
        self._evidence_acquirer = evidence_acquirer
        self._source_discoverer = source_discoverer
        self._max_batch_turns = int(max_batch_turns)
        self._max_tail_turns = int(max_tail_turns)
        self._max_total_turns = int(max_total_turns)
        self._max_accounted_tokens = int(max_accounted_tokens)
        self._max_deterministic_network_requests = int(
            max_deterministic_network_requests
        )
        self._max_batch_stories = int(max_batch_stories)
        self._deterministic_cache: dict[str, dict[str, Any]] = {}
        self._resumed_cache: dict[str, dict[str, Any]] = {}
        self._contracts: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
        self._contract_receipts: dict[
            tuple[str, tuple[str, ...]], dict[str, Any]
        ] = {}
        self._batch_covered: set[tuple[str, tuple[str, ...]]] = set()
        self._tail_covered: set[tuple[str, tuple[str, ...]]] = set()
        self._turns: list[dict[str, Any]] = []
        self._deterministic_frontier: dict[
            tuple[str, tuple[str, ...]], dict[str, Any]
        ] = {}
        self._failures: list[dict[str, Any]] = []
        self._deterministic_acquisition_calls = 0
        self._deterministic_network_requests = 0
        self._deterministic_cache_hits = 0
        self._resumed_cache_hits = 0
        self._discovery_contract_reuse_hits = 0
        self._accounting_complete = True
        self._terminal_budget_blocker: str | None = None
        self._terminal_provider_blocker: str | None = None

    def _handshake(
        self,
        request: Mapping[str, Any],
        receipt: Mapping[str, Any],
        *,
        status: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": "contentops.autonomous_source_discovery_handshake.v1",
            "story_identity": request.get("cluster_id"),
            "headline_ids": list(request.get("headline_ids") or []),
            "initial_receipt_sha256": _hash(receipt),
            "prior_blockers": [str(value) for value in receipt.get("blockers") or []],
            "same_candidate_resume_required": True,
            "source_discovery_available": True,
            "status": status,
            "search_snippet_or_model_summary_authority": False,
            "publication_authority": False,
        }

    def acquire(self, request: Mapping[str, Any]) -> Any:
        request_row = dict(request)
        identity = _identity(request_row)
        request_hash = str(request_row.get("request_logical_hash") or _hash(request_row))
        cache_key = f"{identity[0]}:{_hash(identity[1])}:{request_hash}"
        contract = self._contracts.get(identity)
        if contract is None:
            if cache_key in self._deterministic_cache:
                self._deterministic_cache_hits += 1
                return copy.deepcopy(self._deterministic_cache[cache_key])
            raw = self._evidence_acquirer(request_row)
            if not isinstance(raw, Mapping):
                return raw
            receipt = dict(raw)
            self._deterministic_acquisition_calls += 1
            request_count = _network_request_count(receipt)
            self._deterministic_network_requests += request_count
            blockers = [str(value) for value in receipt.get("blockers") or []]
            if "SOURCE_DISCOVERY_REQUIRED" in blockers:
                self._deterministic_frontier[identity] = {
                    **_identity_row(identity),
                    "request_logical_hash": request_hash,
                    "initial_receipt_sha256": _hash(receipt),
                    "prior_blockers": blockers,
                    "deterministic_network_requests": request_count,
                }
                receipt["autonomous_source_discovery"] = self._handshake(
                    request_row,
                    receipt,
                    status="PENDING_BATCH_DISCOVERY",
                )
            if (
                self._deterministic_network_requests
                > self._max_deterministic_network_requests
            ):
                self._terminal_budget_blocker = (
                    "URL_DISCOVERY_DETERMINISTIC_REQUEST_CEILING_EXCEEDED"
                )
                receipt["status"] = "BLOCKED"
                receipt["blockers"] = sorted(
                    set(
                        [str(value) for value in receipt.get("blockers") or []]
                        + [self._terminal_budget_blocker]
                    )
                )
            self._deterministic_cache[cache_key] = copy.deepcopy(receipt)
            return receipt

        contract_hash = _hash(contract)
        resumed_key = f"{cache_key}:{contract_hash}"
        if resumed_key in self._resumed_cache:
            self._resumed_cache_hits += 1
            self._discovery_contract_reuse_hits += 1
            return copy.deepcopy(self._resumed_cache[resumed_key])
        validate_codex_source_discovery_contract(contract, request=request_row)
        resumed_request = {
            **request_row,
            "codex_source_discovery": copy.deepcopy(contract),
        }
        raw = self._evidence_acquirer(resumed_request)
        if not isinstance(raw, Mapping):
            return raw
        resumed = dict(raw)
        self._deterministic_acquisition_calls += 1
        request_count = _network_request_count(resumed)
        self._deterministic_network_requests += request_count
        if (
            self._deterministic_network_requests
            > self._max_deterministic_network_requests
        ):
            self._terminal_budget_blocker = (
                "URL_DISCOVERY_DETERMINISTIC_REQUEST_CEILING_EXCEEDED"
            )
            resumed["status"] = "BLOCKED"
            resumed["blockers"] = sorted(
                set(
                    [str(value) for value in resumed.get("blockers") or []]
                    + [self._terminal_budget_blocker]
                )
            )
        provider_receipt = self._contract_receipts.get(identity) or {}
        resumed["autonomous_source_discovery"] = {
            **self._handshake(
                request_row,
                self._deterministic_cache.get(cache_key, {}),
                status="SAME_CANDIDATE_RESUMED",
            ),
            "resumed_story_identity": resumed_request.get("cluster_id"),
            "same_candidate_resumed": bool(
                resumed_request.get("cluster_id") == request_row.get("cluster_id")
                and list(resumed_request.get("headline_ids") or [])
                == list(request_row.get("headline_ids") or [])
            ),
            "provider_receipt": copy.deepcopy(provider_receipt),
            "resumed_receipt_sha256": _hash(resumed),
        }
        self._resumed_cache[resumed_key] = copy.deepcopy(resumed)
        return resumed

    def _unresolved_requests(
        self,
        viability: Mapping[str, Any],
        *,
        pass_kind: str,
    ) -> list[dict[str, Any]]:
        rows: list[tuple[int, dict[str, Any]]] = []
        for attempt_value in viability.get("rank_attempts") or []:
            if not isinstance(attempt_value, Mapping):
                continue
            attempt = dict(attempt_value)
            request = attempt.get("request")
            receipt = attempt.get("evidence_receipt")
            if not isinstance(request, Mapping) or not isinstance(receipt, Mapping):
                continue
            receipt_blockers = [str(value) for value in receipt.get("blockers") or []]
            attempt_blockers = [str(value) for value in attempt.get("blockers") or []]
            blockers = list(dict.fromkeys(receipt_blockers + attempt_blockers))
            if not _DISCOVERY_REQUIRED_MARKERS.intersection(blockers):
                continue
            identity = _identity(request)
            if pass_kind == "BATCH" and identity in self._batch_covered:
                continue
            if pass_kind == "TAIL" and (
                identity not in self._batch_covered or identity in self._tail_covered
            ):
                continue
            discovery_request = {
                **dict(request),
                "prior_blockers": blockers,
            }
            if pass_kind == "TAIL" and identity in self._contracts:
                discovery_request["prior_discovered_urls"] = list(
                    self._contracts[identity].get("candidate_urls") or []
                )
            health_snapshotter = getattr(
                self._evidence_acquirer, "source_route_health_snapshot", None
            )
            if callable(health_snapshotter):
                snapshot = health_snapshotter()
                discovery_request["source_route_health_hosts"] = [
                    dict(row)
                    for row in (snapshot or {}).get("hosts") or []
                    if isinstance(row, Mapping)
                ]
            rows.append((int(attempt.get("rank") or 0), discovery_request))
        rows.sort(key=lambda value: (value[0], _identity(value[1])))
        unique: list[dict[str, Any]] = []
        seen: set[tuple[str, tuple[str, ...]]] = set()
        for _, request in rows:
            identity = _identity(request)
            if identity in seen:
                continue
            seen.add(identity)
            unique.append(request)
        return unique[: self._max_batch_stories]

    def _record_turn(
        self,
        *,
        pass_kind: str,
        requests: list[Mapping[str, Any]],
        provider_receipt: Mapping[str, Any],
        status: str,
        resolved_count: int,
        failure_code: str | None = None,
    ) -> None:
        usage = provider_receipt.get("turn_result_usage") or {}
        token_value = usage.get("total_tokens") if isinstance(usage, Mapping) else None
        if token_value is None:
            self._accounting_complete = False
            accounted_tokens = 0
        else:
            accounted_tokens = int(token_value or 0)
        self._turns.append(
            {
                "turn_number": len(self._turns) + 1,
                "pass_kind": pass_kind,
                "status": status,
                "candidate_story_count": len(requests),
                "candidate_story_membership": [
                    _identity_row(_identity(request)) for request in requests
                ],
                "candidate_story_membership_sha256": _hash(
                    [_identity(request) for request in requests]
                ),
                "resolved_story_count": int(resolved_count),
                "accounted_discovery_tokens": accounted_tokens,
                "provider_receipt": copy.deepcopy(dict(provider_receipt)),
                "failure_code": failure_code,
                "search_snippets_persisted": False,
                "model_summaries_persisted": False,
                "candidate_urls_are_evidence": False,
                "publication_authority_granted": False,
            }
        )

    def discover_unresolved(
        self,
        viability: Mapping[str, Any],
        *,
        pass_kind: str,
    ) -> dict[str, Any]:
        normalized_pass_kind = str(pass_kind or "").upper()
        if normalized_pass_kind not in {"BATCH", "TAIL"}:
            raise ValueError("quota_discovery_pass_kind_invalid")
        if (
            self._terminal_budget_blocker is not None
            or self._terminal_provider_blocker is not None
        ):
            return {
                "called": False,
                "new_contract_count": 0,
                "blocker": self._terminal_budget_blocker
                or self._terminal_provider_blocker,
            }
        requests = self._unresolved_requests(
            viability, pass_kind=normalized_pass_kind
        )
        if not requests:
            return {"called": False, "new_contract_count": 0}
        batch_turn_count = sum(row["pass_kind"] == "BATCH" for row in self._turns)
        tail_turn_count = sum(row["pass_kind"] == "TAIL" for row in self._turns)
        if (
            len(self._turns) >= self._max_total_turns
            or normalized_pass_kind == "BATCH"
            and batch_turn_count >= self._max_batch_turns
            or normalized_pass_kind == "TAIL"
            and tail_turn_count >= self._max_tail_turns
        ):
            self._terminal_budget_blocker = "URL_DISCOVERY_TURN_CEILING_EXCEEDED"
            return {
                "called": False,
                "new_contract_count": 0,
                "blocker": self._terminal_budget_blocker,
            }
        identities = {_identity(request) for request in requests}
        if normalized_pass_kind == "BATCH":
            self._batch_covered.update(identities)
        else:
            self._tail_covered.update(identities)

        provider_receipt: dict[str, Any] = {}
        result: dict[str, Any] = {}
        try:
            batch_call = getattr(self._source_discoverer, "discover_batch", None)
            if callable(batch_call):
                raw = batch_call(requests, pass_kind=normalized_pass_kind)
            elif len(requests) == 1 and callable(self._source_discoverer):
                raw_single = self._source_discoverer(requests[0])
                raw = {
                    "contracts": [dict((raw_single or {}).get("contract") or {})],
                    "provider_receipt": dict(
                        (raw_single or {}).get("provider_receipt") or {}
                    ),
                }
            else:
                self._terminal_provider_blocker = (
                    "BATCH_DISCOVERY_INTERFACE_REQUIRED"
                )
                self._failures.append(
                    {
                        "pass_kind": normalized_pass_kind,
                        "failure_code": "BATCH_DISCOVERY_INTERFACE_REQUIRED",
                        "candidate_story_membership": [
                            _identity_row(identity) for identity in sorted(identities)
                        ],
                    }
                )
                return {
                    "called": False,
                    "new_contract_count": 0,
                    "blocker": self._terminal_provider_blocker,
                }
            result = dict(raw) if isinstance(raw, Mapping) else {}
            provider_receipt = dict(result.get("provider_receipt") or {})
            batch_contract = result.get("batch_contract")
            if isinstance(batch_contract, Mapping):
                validate_codex_source_discovery_batch_contract(
                    batch_contract,
                    requests=requests,
                    pass_kind=normalized_pass_kind,
                )
        except Exception as exc:
            provider_receipt = dict(getattr(exc, "receipt", None) or {})
            failure_code = str(getattr(exc, "code", type(exc).__name__))
            model_turn_completed = bool(
                getattr(exc, "model_turn_completed", False) or provider_receipt
            )
            if model_turn_completed:
                self._record_turn(
                    pass_kind=normalized_pass_kind,
                    requests=requests,
                    provider_receipt=provider_receipt,
                    status="FAILED",
                    resolved_count=0,
                    failure_code=failure_code,
                )
            if failure_code in {
                "API_KEY_ENVIRONMENT_PRESENT",
                "CHATGPT_AUTH_REQUIRED_API_KEY_FALLBACK_FORBIDDEN",
                "CHATGPT_USAGE_LIMIT_REACHED",
                "OPENAI_CODEX_SDK_NOT_INSTALLED",
                "OPENAI_CODEX_SDK_VERSION_MISMATCH",
                "CODEX_MODEL_OR_EFFORT_UNAVAILABLE",
            }:
                self._terminal_provider_blocker = failure_code
            self._failures.append(
                {
                    "pass_kind": normalized_pass_kind,
                    "failure_class": type(exc).__name__,
                    "failure_code": failure_code,
                    "model_turn_completed": model_turn_completed,
                    "candidate_story_membership": [
                        _identity_row(identity) for identity in sorted(identities)
                    ],
                }
            )
            return {"called": model_turn_completed, "new_contract_count": 0}

        contracts = [
            dict(value)
            for value in result.get("contracts") or []
            if isinstance(value, Mapping)
        ]
        request_by_identity = {_identity(request): request for request in requests}
        validated_contracts: list[
            tuple[tuple[str, tuple[str, ...]], dict[str, Any]]
        ] = []
        try:
            for contract in contracts:
                identity = (
                    str(contract.get("story_identity") or ""),
                    tuple(
                        sorted(
                            str(value)
                            for value in contract.get("headline_ids") or []
                        )
                    ),
                )
                if identity not in request_by_identity:
                    raise ValueError("quota_discovery_provider_cross_story_binding")
                validate_codex_source_discovery_contract(
                    contract, request=request_by_identity[identity]
                )
                if sorted(
                    set(str(value) for value in contract.get("prior_blockers") or [])
                ) != sorted(
                    set(
                        str(value)
                        for value in request_by_identity[identity].get(
                            "prior_blockers"
                        )
                        or []
                    )
                ):
                    raise ValueError(
                        "quota_discovery_provider_prior_blockers_mismatch"
                    )
                validated_contracts.append((identity, contract))
        except ValueError as exc:
            self._record_turn(
                pass_kind=normalized_pass_kind,
                requests=requests,
                provider_receipt=provider_receipt,
                status="FAILED",
                resolved_count=0,
                failure_code=str(exc),
            )
            self._failures.append(
                {
                    "pass_kind": normalized_pass_kind,
                    "failure_class": type(exc).__name__,
                    "failure_code": str(exc),
                    "candidate_story_membership": [
                        _identity_row(identity) for identity in sorted(identities)
                    ],
                }
            )
            return {"called": True, "new_contract_count": 0}

        self._record_turn(
            pass_kind=normalized_pass_kind,
            requests=requests,
            provider_receipt=provider_receipt,
            status="PASS",
            resolved_count=len(validated_contracts),
        )
        total_tokens = sum(
            int(row.get("accounted_discovery_tokens") or 0) for row in self._turns
        )
        if total_tokens > self._max_accounted_tokens:
            self._terminal_budget_blocker = "URL_DISCOVERY_TOKEN_CEILING_EXCEEDED"
            self._failures.append(
                {
                    "pass_kind": normalized_pass_kind,
                    "failure_code": self._terminal_budget_blocker,
                    "accounted_discovery_tokens": total_tokens,
                }
            )
            return {
                "called": True,
                "new_contract_count": 0,
                "blocker": self._terminal_budget_blocker,
            }
        for identity, contract in validated_contracts:
            self._contracts[identity] = copy.deepcopy(contract)
            self._contract_receipts[identity] = copy.deepcopy(provider_receipt)
            self._resumed_cache = {
                key: value
                for key, value in self._resumed_cache.items()
                if not key.endswith(":" + _hash(contract))
            }
        return {
            "called": True,
            "new_contract_count": len(validated_contracts),
        }

    def snapshot(self, *, ready_candidate_count: int = 0) -> dict[str, Any]:
        batch_turn_count = sum(row["pass_kind"] == "BATCH" for row in self._turns)
        tail_turn_count = sum(row["pass_kind"] == "TAIL" for row in self._turns)
        total_tokens = sum(
            int(row.get("accounted_discovery_tokens") or 0) for row in self._turns
        )
        economics_accepted = bool(
            self._accounting_complete
            and batch_turn_count <= self._max_batch_turns
            and tail_turn_count <= self._max_tail_turns
            and len(self._turns) <= self._max_total_turns
            and total_tokens <= self._max_accounted_tokens
            and self._deterministic_network_requests
            <= self._max_deterministic_network_requests
            and self._terminal_budget_blocker is None
            and self._terminal_provider_blocker is None
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "PASS" if economics_accepted else "BLOCKED",
            "batch_discovery_turns": batch_turn_count,
            "tail_discovery_turns": tail_turn_count,
            "total_discovery_turns": len(self._turns),
            "accounted_discovery_tokens": total_tokens,
            "accounting_complete": self._accounting_complete,
            "candidates_covered_per_turn": [
                int(row["candidate_story_count"]) for row in self._turns
            ],
            "turns": copy.deepcopy(self._turns),
            "deterministic_acquisition_calls": self._deterministic_acquisition_calls,
            "deterministic_network_requests": self._deterministic_network_requests,
            "ready_candidate_yield": int(ready_candidate_count),
            "cache_and_reuse": {
                "deterministic_receipt_cache_hits": self._deterministic_cache_hits,
                "resumed_receipt_cache_hits": self._resumed_cache_hits,
                "discovery_contract_reuse_hits": self._discovery_contract_reuse_hits,
            },
            "deterministic_frontier": sorted(
                copy.deepcopy(list(self._deterministic_frontier.values())),
                key=lambda row: (row["story_identity"], row["headline_ids"]),
            ),
            "batch_covered_story_membership": [
                _identity_row(identity) for identity in sorted(self._batch_covered)
            ],
            "tail_covered_story_membership": [
                _identity_row(identity) for identity in sorted(self._tail_covered)
            ],
            "failures": copy.deepcopy(self._failures),
            "terminal_budget_blocker": self._terminal_budget_blocker,
            "terminal_provider_blocker": self._terminal_provider_blocker,
            "budget": {
                "max_batch_turns": self._max_batch_turns,
                "max_tail_turns": self._max_tail_turns,
                "max_total_turns": self._max_total_turns,
                "max_accounted_discovery_tokens": self._max_accounted_tokens,
                "max_deterministic_network_requests": (
                    self._max_deterministic_network_requests
                ),
                "max_stories_per_turn": self._max_batch_stories,
            },
            "accepted_baseline_comparison": {
                "baseline_discovery_turns": 35,
                "baseline_accounted_discovery_tokens": 10_237_897,
                "discovery_turn_delta": len(self._turns) - 35,
                "accounted_discovery_token_delta": total_tokens - 10_237_897,
                "monetary_savings_claimed": False,
                "exact_price_or_cost_receipt_available": False,
            },
            "tail_is_subset_only": self._tail_covered.issubset(
                self._batch_covered
            ),
            "each_story_reaches_tail_at_most_once": True,
            "search_snippets_persisted": False,
            "model_summaries_persisted": False,
            "candidate_urls_are_evidence": False,
            "factual_or_numeric_authority_granted": False,
            "publication_authority_granted": False,
            "public_write_attempted": False,
        }
