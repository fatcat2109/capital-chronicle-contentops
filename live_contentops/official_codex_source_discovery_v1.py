"""Supported ChatGPT-authenticated Codex/App-Server URL-only source discovery.

The role may locate URLs after deterministic acquisition proves no viable path. Search output is
never evidence: only the bounded URL contract crosses into the canonical deterministic retriever.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Mapping

from live_contentops.official_codex_provider_v1 import (
    API_KEY_ENVIRONMENT_NAMES,
    OFFICIAL_SDK_VERSION,
    OfficialCodexProviderError,
    _enum_value,
    _item_type,
    _usage,
)
from live_contentops.rolling_x_targeted_evidence_adapter_v1 import (
    CODEX_SOURCE_DISCOVERY_SCHEMA_VERSION,
    validate_codex_source_discovery_contract,
)


MODEL = "gpt-5.6-sol"
EFFORT = "high"
ROLE = "V1_URL_ONLY_SOURCE_DISCOVERY"
TRANSPORT = "OFFICIAL_CODEX_APP_SERVER_STDIO_WEB_SEARCH"
ALLOWED_RESULT_ITEM_TYPES = frozenset(
    {"usermessage", "reasoning", "websearch", "agentmessage"}
)


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
        ).encode("utf-8")
    ).hexdigest()


URL_DISCOVERY_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "story_identity",
        "headline_ids",
        "trigger_reason",
        "prior_blockers",
        "candidate_urls",
        "search_call_id",
        "searched_at_utc",
        "search_snippets_included",
        "model_summaries_included",
        "candidate_urls_are_evidence",
        "factual_or_numeric_authority_granted",
        "publication_authority_granted",
    ],
    "properties": {
        "schema_version": {"type": "string", "enum": [CODEX_SOURCE_DISCOVERY_SCHEMA_VERSION]},
        "story_identity": {"type": "string"},
        "headline_ids": {"type": "array", "items": {"type": "string"}},
        "trigger_reason": {
            "type": "string",
            "enum": ["NO_VIABLE_DETERMINISTIC_PATH", "BOUNDED_ACCESS_FAILURE"],
        },
        "prior_blockers": {"type": "array", "items": {"type": "string"}},
        "candidate_urls": {
            "type": "array",
            "minItems": 1,
            "maxItems": 4,
            "items": {"type": "string"},
        },
        "search_call_id": {"type": "string"},
        "searched_at_utc": {"type": "string"},
        "search_snippets_included": {"type": "boolean", "enum": [False]},
        "model_summaries_included": {"type": "boolean", "enum": [False]},
        "candidate_urls_are_evidence": {"type": "boolean", "enum": [False]},
        "factual_or_numeric_authority_granted": {"type": "boolean", "enum": [False]},
        "publication_authority_granted": {"type": "boolean", "enum": [False]},
    },
}


class OfficialCodexUrlDiscoveryProvider:
    """One fresh HIGH search turn per exact discovery trigger; no editorial role or authority."""

    DEVELOPER_INSTRUCTIONS = (
        "You are a URL-only source locator for Capital Chronicle ContentOps. Use live web search "
        "only to locate exact current publisher or registered official source URLs for the supplied "
        "story. Return only the strict JSON object. Never include snippets, summaries, claims, "
        "numbers, analysis, prose, or evidence. Candidate URLs are locators only and grant no "
        "factual, numeric, permission, publication, or public-write authority. Prefer exact article "
        "or release URLs from the registered hosts implied by the request; do not invent URLs. "
        "You MUST use only the built-in web search/open-page capability. Never invoke command "
        "execution, a terminal, shell, scripts, file tools, computer use, browser automation, MCP, "
        "or any other tool. Do not use a command to verify, expand, fetch, or inspect a URL. If web "
        "search alone cannot locate an eligible URL, return the best exact eligible URL already "
        "observed in web search; do not seek another transport."
    )

    def __init__(
        self,
        *,
        output_dir: Path,
        sdk_factory: Callable[[], Any] | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self.output_dir = Path(output_dir).resolve()
        self.sdk_factory = sdk_factory
        self.environment = dict(os.environ if environment is None else environment)
        self.call_count = 0

    def _sdk(self) -> tuple[Any, Any, Any, Any, str]:
        if self.sdk_factory is not None:
            supplied = self.sdk_factory()
            if isinstance(supplied, tuple) and len(supplied) == 5:
                return supplied
        try:
            from openai_codex import ApprovalMode, Codex, Sandbox, __version__ as sdk_version
            from openai_codex.types import ReasoningEffort
        except ImportError as exc:
            raise OfficialCodexProviderError(
                "OPENAI_CODEX_SDK_NOT_INSTALLED", phase="APP_SERVER_TRANSPORT"
            ) from exc
        return Codex(), ApprovalMode, Sandbox, ReasoningEffort, str(sdk_version)

    def __call__(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self.call_count += 1
        if any(name in self.environment for name in API_KEY_ENVIRONMENT_NAMES):
            raise OfficialCodexProviderError(
                "API_KEY_ENVIRONMENT_PRESENT", phase="AUTH_PREFLIGHT"
            )
        sdk, approval_mode, sandbox, reasoning_effort, sdk_version = self._sdk()
        if sdk_version != OFFICIAL_SDK_VERSION:
            raise OfficialCodexProviderError(
                "OPENAI_CODEX_SDK_VERSION_MISMATCH", phase="APP_SERVER_TRANSPORT"
            )
        story_identity = str(request.get("cluster_id") or "")
        prior_blockers = [str(value) for value in request.get("prior_blockers") or []]
        prompt_input = {
            "story_identity": story_identity,
            "headline_ids": [str(value) for value in request.get("headline_ids") or []],
            "why_now": str((request.get("story_context") or {}).get("why_now") or ""),
            "selection_case": str(
                (request.get("story_context") or {}).get("selection_case") or ""
            ),
            "leaf_summaries": [
                str(value)
                for value in (request.get("story_context") or {}).get("leaf_summaries") or []
            ],
            "prior_blockers": prior_blockers,
            "required_source_adapter_families": list(
                request.get("source_adapter_families") or []
            ),
            "routing_only_host_health": [
                {
                    "host": str(row.get("normalized_host") or ""),
                    "success_count": int(row.get("success_count") or 0),
                    "failure_count": int(row.get("failure_count") or 0),
                    "last_failure_class": str(row.get("last_failure_class") or ""),
                }
                for row in request.get("source_route_health_hosts") or []
                if isinstance(row, Mapping)
                and str(row.get("normalized_host") or "")
            ],
        }
        from live_contentops.official_primary_evidence_loader_v1 import (
            OFFICIAL_HOSTS_BY_FAMILY,
        )
        from live_contentops.public_secondary_evidence_loader_v1 import (
            REPUTABLE_SECONDARY_HOSTS,
        )

        prompt_input["eligible_url_hosts"] = sorted(
            set(REPUTABLE_SECONDARY_HOSTS).union(
                host
                for hosts in OFFICIAL_HOSTS_BY_FAMILY.values()
                for host in hosts
            )
        )
        prompt = (
            "Locate one to four exact current eligible source URLs for this story. Search live, "
            "then return the required URL-only JSON contract with the exact supplied identity and "
            "prior blockers. Use trigger_reason BOUNDED_ACCESS_FAILURE when the blockers show "
            "access/status failures, otherwise NO_VIABLE_DETERMINISTIC_PATH. Every candidate URL "
            "hostname MUST exactly match one eligible_url_hosts value; omit every result on any "
            "other host. Prefer a precise article/release URL over a home, search, tag, or listing "
            "page. Treat routing_only_host_health only as work-order evidence: never as factual "
            "evidence and never as a host-wide prohibition. Prefer exact current alternatives on "
            "hosts with observed success, especially AP News, The Guardian, Al Jazeera, BBC, NPR, "
            "Politico, or an eligible official host. If the named/original publisher has repeated "
            "access failures, locate independent current corroboration instead; a distinct exact "
            "same-publisher route remains allowed.\n\n"
            "Tool constraint: use built-in web search/open-page only. Do not invoke any command, "
            "terminal, shell, file, computer-use, browser-automation, or MCP action.\n\n"
            + json.dumps(prompt_input, sort_keys=True, ensure_ascii=False)
        )
        proof_cwd = self.output_dir / (
            f"codex_url_discovery_{self.call_count:02d}_{_hash(prompt_input)[:12]}"
        )
        proof_cwd.mkdir(parents=True, exist_ok=False)
        sdk_context = sdk
        codex = None
        started = time.perf_counter()
        try:
            codex = sdk_context.__enter__()
            account_wrapper = codex.account(refresh_token=False)
            account = getattr(account_wrapper, "account", None)
            account = None if account is None else getattr(account, "root", account)
            if str(_enum_value(getattr(account, "type", ""))).lower() != "chatgpt":
                raise OfficialCodexProviderError(
                    "CHATGPT_AUTH_REQUIRED_API_KEY_FALLBACK_FORBIDDEN",
                    phase="AUTH_PREFLIGHT",
                )
            catalog = {
                str(getattr(item, "id", "")): tuple(
                    str(_enum_value(getattr(row, "reasoning_effort", row))).lower()
                    for row in (
                        getattr(item, "supported_reasoning_efforts", None) or ()
                    )
                )
                for item in getattr(codex.models(include_hidden=False), "data", ())
            }
            if MODEL not in catalog or EFFORT not in catalog[MODEL]:
                raise OfficialCodexProviderError(
                    "CODEX_MODEL_OR_EFFORT_UNAVAILABLE", phase="MODEL_DISCOVERY"
                )
            thread = codex.thread_start(
                approval_mode=approval_mode.deny_all,
                config={"web_search": "live"},
                cwd=str(proof_cwd),
                developer_instructions=self.DEVELOPER_INSTRUCTIONS,
                ephemeral=True,
                model=MODEL,
                sandbox=sandbox.read_only,
            )
            result = thread.run(
                prompt,
                approval_mode=approval_mode.deny_all,
                effort=getattr(reasoning_effort, EFFORT),
                model=MODEL,
                output_schema=URL_DISCOVERY_OUTPUT_SCHEMA,
                sandbox=sandbox.read_only,
            )
            status = str(_enum_value(getattr(result, "status", ""))).lower()
            if status != "completed" or getattr(result, "error", None) is not None:
                raise OfficialCodexProviderError(
                    "CODEX_TURN_NOT_COMPLETED", phase="TURN_EXECUTION"
                )
            content = getattr(result, "final_response", None)
            if not isinstance(content, str):
                raise OfficialCodexProviderError(
                    "CODEX_FINAL_RESPONSE_MISSING",
                    phase="STRUCTURED_OUTPUT",
                    model_turn_completed=True,
                )
            contract = json.loads(content)
            item_types = [_item_type(item) for item in getattr(result, "items", ())]
            turn_usage = _usage(getattr(result, "usage", None))
            duration_ms = int(
                getattr(result, "duration_ms", None)
                or round((time.perf_counter() - started) * 1000)
            )
            try:
                normalized = validate_codex_source_discovery_contract(
                    contract, request=request
                )
            except ValueError as exc:
                failure_receipt = {
                    "schema_version": "contentops.official_codex_url_discovery_receipt.v1",
                    "provider": "OPENAI_CODEX_CHATGPT",
                    "transport": TRANSPORT,
                    "sdk_version": sdk_version,
                    "auth_classification": "CHATGPT",
                    "model": MODEL,
                    "reasoning_effort": EFFORT.upper(),
                    "role": ROLE,
                    "status": "LOCAL_CONTRACT_REJECTED",
                    "validation_failure": str(exc),
                    "thread_ephemeral": True,
                    "sandbox": "read_only",
                    "approval_mode": "deny_all",
                    "web_search_mode": "live",
                    "turn_result_item_types": item_types,
                    "turn_result_usage": turn_usage,
                    "turn_result_duration_ms": duration_ms,
                    "story_identity": story_identity,
                    "search_snippets_persisted": False,
                    "model_summaries_persisted": False,
                    "candidate_urls_persisted": False,
                    "candidate_urls_are_evidence": False,
                    "factual_or_numeric_authority_granted": False,
                    "permission_authority_granted": False,
                    "publication_authority_granted": False,
                    "public_write_attempted": False,
                    "api_key_fallback_calls": 0,
                }
                raise OfficialCodexProviderError(
                    "CODEX_SOURCE_DISCOVERY_CONTRACT_INVALID",
                    phase="LOCAL_VALIDATION",
                    model_turn_completed=True,
                    receipt=failure_receipt,
                ) from exc
            validation_receipt = {
                "schema_version": "contentops.official_codex_url_discovery_receipt.v1",
                "provider": "OPENAI_CODEX_CHATGPT",
                "transport": TRANSPORT,
                "sdk_version": sdk_version,
                "auth_classification": "CHATGPT",
                "model": MODEL,
                "reasoning_effort": EFFORT.upper(),
                "role": ROLE,
                "status": "LOCAL_ACTION_VALIDATION_REJECTED",
                "thread_ephemeral": True,
                "sandbox": "read_only",
                "approval_mode": "deny_all",
                "web_search_mode": "live",
                "turn_result_item_types": item_types,
                "turn_result_usage": turn_usage,
                "turn_result_duration_ms": duration_ms,
                "story_identity": story_identity,
                "discovery_contract_sha256": normalized[
                    "discovery_contract_sha256"
                ],
                "candidate_url_count": len(normalized["candidates"]),
                "search_snippets_persisted": False,
                "model_summaries_persisted": False,
                "candidate_urls_are_evidence": False,
                "factual_or_numeric_authority_granted": False,
                "permission_authority_granted": False,
                "publication_authority_granted": False,
                "public_write_attempted": False,
                "api_key_fallback_calls": 0,
            }
            if not any("web" in value.casefold() and "search" in value.casefold() for value in item_types):
                raise OfficialCodexProviderError(
                    "CODEX_SOURCE_DISCOVERY_WEB_SEARCH_NOT_OBSERVED",
                    phase="LOCAL_VALIDATION",
                    model_turn_completed=True,
                    receipt=validation_receipt,
                )
            if any(
                value.casefold() not in ALLOWED_RESULT_ITEM_TYPES
                for value in item_types
            ):
                raise OfficialCodexProviderError(
                    "CODEX_SOURCE_DISCOVERY_UNEXPECTED_ACTION_ITEM",
                    phase="LOCAL_VALIDATION",
                    model_turn_completed=True,
                    receipt=validation_receipt,
                )
            if any(proof_cwd.iterdir()):
                raise OfficialCodexProviderError(
                    "CODEX_READ_ONLY_CWD_MUTATED",
                    phase="LOCAL_VALIDATION",
                    model_turn_completed=True,
                    receipt=validation_receipt,
                )
            receipt = {
                "schema_version": "contentops.official_codex_url_discovery_receipt.v1",
                "provider": "OPENAI_CODEX_CHATGPT",
                "transport": TRANSPORT,
                "sdk_version": sdk_version,
                "auth_classification": "CHATGPT",
                "model": MODEL,
                "reasoning_effort": EFFORT.upper(),
                "role": ROLE,
                "thread_ephemeral": True,
                "sandbox": "read_only",
                "approval_mode": "deny_all",
                "web_search_mode": "live",
                "turn_result_item_types": item_types,
                "turn_result_usage": turn_usage,
                "turn_result_duration_ms": duration_ms,
                "story_identity": story_identity,
                "discovery_contract_sha256": normalized[
                    "discovery_contract_sha256"
                ],
                "candidate_url_count": len(normalized["candidates"]),
                "search_snippets_persisted": False,
                "model_summaries_persisted": False,
                "candidate_urls_are_evidence": False,
                "factual_or_numeric_authority_granted": False,
                "permission_authority_granted": False,
                "publication_authority_granted": False,
                "public_write_attempted": False,
                "api_key_fallback_calls": 0,
            }
            return {"contract": dict(contract), "provider_receipt": receipt}
        except json.JSONDecodeError as exc:
            raise OfficialCodexProviderError(
                "CODEX_FINAL_RESPONSE_NOT_JSON",
                phase="STRUCTURED_OUTPUT",
                model_turn_completed=True,
            ) from exc
        finally:
            if codex is not None:
                sdk_context.__exit__(None, None, None)
