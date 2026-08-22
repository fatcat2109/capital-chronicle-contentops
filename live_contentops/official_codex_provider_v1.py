"""Thin official Codex SDK/App Server provider for the canonical V1 editorial seam.

The provider owns no newsroom, scheduling, evidence, validation, packaging, or publication
authority. It submits one bounded editorial turn to the local official App Server using managed
ChatGPT authentication, then returns the official ``TurnResult`` to the existing deterministic
article builder. One optional revision resumes the same ephemeral SDK thread.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


OFFICIAL_SDK_VERSION = "0.147.0"
PROVIDER_ID = "OPENAI_CODEX_CHATGPT"
TRANSPORT = "OFFICIAL_CODEX_APP_SERVER_STDIO"
AUTH_CLASSIFICATION = "CHATGPT"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
API_KEY_ENVIRONMENT_NAMES = ("OPENAI_API_KEY", "CODEX_API_KEY")
TRANSPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"article_json": {"type": "string"}},
    "required": ["article_json"],
    "additionalProperties": False,
}
PHASES = frozenset(
    {
        "AUTH_PREFLIGHT",
        "MODEL_DISCOVERY",
        "THREAD_START",
        "TURN_START",
        "TURN_EXECUTION",
        "STRUCTURED_OUTPUT",
        "TURN_RESULT_NORMALIZATION",
        "POST_TURN_METADATA_READBACK",
        "APP_SERVER_TRANSPORT",
        "TIMEOUT",
        "RATE_LIMIT",
        "CONTEXT_LIMIT",
        "LOCAL_VALIDATION",
    }
)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )


def _sha256(value: str | Mapping[str, Any]) -> str:
    if isinstance(value, Mapping):
        value = _canonical_json(value)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _item_type(item: Any) -> str:
    root = getattr(item, "root", item)
    return str(_enum_value(getattr(root, "type", root.__class__.__name__)))


def _usage(value: Any) -> dict[str, int]:
    total = getattr(value, "total", None)
    if total is None:
        return {}
    return {
        name: int(getattr(total, name, 0) or 0)
        for name in (
            "input_tokens",
            "cached_input_tokens",
            "cache_write_input_tokens",
            "output_tokens",
            "reasoning_output_tokens",
            "total_tokens",
        )
    }


class OfficialCodexProviderError(RuntimeError):
    """Sanitized provider failure with an exact lifecycle phase."""

    def __init__(
        self,
        code: str,
        *,
        phase: str,
        model_turn_completed: bool = False,
        receipt: Mapping[str, Any] | None = None,
    ) -> None:
        if phase not in PHASES:
            raise ValueError("official_codex_provider_phase_invalid")
        super().__init__(code)
        self.code = code
        self.phase = phase
        self.model_turn_completed = bool(model_turn_completed)
        self.receipt = dict(receipt or {})


@dataclass(frozen=True)
class OfficialCodexTurnExecution:
    output: Mapping[str, Any]
    receipt: Mapping[str, Any]


class OfficialCodexEditorialSession:
    """One ephemeral ChatGPT-authenticated SDK thread and at most two logical turns."""

    def __init__(
        self,
        *,
        proof_cwd: Path,
        sdk_factory: Callable[[], Any] | None = None,
        environment: Mapping[str, str] | None = None,
        expected_sdk_version: str = OFFICIAL_SDK_VERSION,
    ) -> None:
        self.proof_cwd = Path(proof_cwd).resolve()
        self.sdk_factory = sdk_factory
        self.environment = dict(os.environ if environment is None else environment)
        self.expected_sdk_version = expected_sdk_version
        self._sdk_context: Any = None
        self._codex: Any = None
        self._thread: Any = None
        self._approval_mode: Any = None
        self._sandbox: Any = None
        self._reasoning_effort: Any = None
        self._sdk_version = expected_sdk_version
        self._thread_id_hash: str | None = None
        self._seen_attempt_keys: set[str] = set()
        self._turn_count = 0
        self._closed = False

    def __enter__(self) -> "OfficialCodexEditorialSession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        del exc_type, exc, traceback
        self.close()

    def _sdk(self) -> tuple[Any, Any, Any, Any, str]:
        if self.sdk_factory is not None:
            supplied = self.sdk_factory()
            if isinstance(supplied, tuple) and len(supplied) == 5:
                return supplied

            class ApprovalMode:
                deny_all = "deny_all"

            class Sandbox:
                read_only = "read_only"

            class ReasoningEffort:
                xhigh = "xhigh"

            return (
                supplied,
                ApprovalMode,
                Sandbox,
                ReasoningEffort,
                self.expected_sdk_version,
            )
        try:
            from openai_codex import (
                ApprovalMode,
                Codex,
                Sandbox,
                __version__ as sdk_version,
            )
            from openai_codex.types import ReasoningEffort
        except ImportError as exc:
            raise OfficialCodexProviderError(
                "OPENAI_CODEX_SDK_NOT_INSTALLED", phase="APP_SERVER_TRANSPORT"
            ) from exc
        if str(sdk_version) != self.expected_sdk_version:
            raise OfficialCodexProviderError(
                "OPENAI_CODEX_SDK_VERSION_MISMATCH", phase="APP_SERVER_TRANSPORT"
            )
        return Codex(), ApprovalMode, Sandbox, ReasoningEffort, str(sdk_version)

    @staticmethod
    def _account(root: Any) -> Any:
        wrapper = root.account(refresh_token=False)
        account = getattr(wrapper, "account", None)
        return None if account is None else getattr(account, "root", account)

    @staticmethod
    def _catalog(root: Any) -> dict[str, tuple[str, ...]]:
        response = root.models(include_hidden=False)
        result: dict[str, tuple[str, ...]] = {}
        for item in getattr(response, "data", ()):
            identifier = str(getattr(item, "id", ""))
            efforts = tuple(
                str(_enum_value(getattr(row, "reasoning_effort", row))).lower()
                for row in (getattr(item, "supported_reasoning_efforts", None) or ())
            )
            if identifier:
                result[identifier] = efforts
        return result

    def _ensure_transport(self) -> None:
        if self._codex is not None:
            return
        if any(name in self.environment for name in API_KEY_ENVIRONMENT_NAMES):
            raise OfficialCodexProviderError(
                "API_KEY_ENVIRONMENT_PRESENT", phase="AUTH_PREFLIGHT"
            )
        sdk, approval_mode, sandbox, reasoning_effort, sdk_version = self._sdk()
        self._sdk_context = sdk
        self._approval_mode = approval_mode
        self._sandbox = sandbox
        self._reasoning_effort = reasoning_effort
        self._sdk_version = sdk_version
        try:
            self._codex = sdk.__enter__()
        except Exception as exc:
            raise OfficialCodexProviderError(
                "CODEX_APP_SERVER_START_FAILED", phase="APP_SERVER_TRANSPORT"
            ) from exc
        account = self._account(self._codex)
        if str(_enum_value(getattr(account, "type", ""))).lower() != "chatgpt":
            raise OfficialCodexProviderError(
                "CHATGPT_AUTH_REQUIRED_API_KEY_FALLBACK_FORBIDDEN",
                phase="AUTH_PREFLIGHT",
            )
        catalog = self._catalog(self._codex)
        if MODEL not in catalog or EFFORT not in catalog[MODEL]:
            raise OfficialCodexProviderError(
                "CODEX_MODEL_OR_EFFORT_UNAVAILABLE", phase="MODEL_DISCOVERY"
            )

    def preflight(self) -> dict[str, Any]:
        self._ensure_transport()
        return {
            "status": "PASS",
            "phase": "MODEL_DISCOVERY",
            "provider": PROVIDER_ID,
            "transport": TRANSPORT,
            "sdk_version": self._sdk_version,
            "auth_classification": AUTH_CLASSIFICATION,
            "api_key_fallback_calls": 0,
            "model": MODEL,
            "reasoning_effort": EFFORT.upper(),
        }

    def _ensure_thread(self, developer_instructions: str) -> None:
        self._ensure_transport()
        if self._thread is not None:
            return
        self.proof_cwd.mkdir(parents=True, exist_ok=True)
        if any(self.proof_cwd.iterdir()):
            raise OfficialCodexProviderError(
                "CODEX_READ_ONLY_CWD_NOT_EMPTY", phase="LOCAL_VALIDATION"
            )
        try:
            self._thread = self._codex.thread_start(
                approval_mode=self._approval_mode.deny_all,
                cwd=str(self.proof_cwd),
                developer_instructions=developer_instructions,
                ephemeral=True,
                model=MODEL,
                sandbox=self._sandbox.read_only,
            )
        except Exception as exc:
            raise OfficialCodexProviderError(
                "CODEX_THREAD_START_FAILED", phase="THREAD_START"
            ) from exc
        self._thread_id_hash = _sha256(str(self._thread.id))

    def run(
        self,
        *,
        prompt: str,
        developer_instructions: str,
        governed_input_hash: str,
        evidence_hash: str,
        role: str,
        revision: bool = False,
    ) -> OfficialCodexTurnExecution:
        if self._closed:
            raise OfficialCodexProviderError(
                "CODEX_SESSION_ALREADY_CLOSED", phase="LOCAL_VALIDATION"
            )
        attempt_key = _sha256(
            {
                "provider": PROVIDER_ID,
                "model": MODEL,
                "effort": EFFORT,
                "role": role,
                "governed_input_hash": governed_input_hash,
                "evidence_hash": evidence_hash,
                "prompt_sha256": _sha256(prompt),
                "schema_sha256": _sha256(TRANSPORT_SCHEMA),
            }
        )
        if attempt_key in self._seen_attempt_keys:
            raise OfficialCodexProviderError(
                "DUPLICATE_LOGICAL_PROVIDER_CALL_BLOCKED", phase="LOCAL_VALIDATION"
            )
        if revision and self._turn_count != 1:
            raise OfficialCodexProviderError(
                "SAME_THREAD_REVISION_REQUIRES_ONE_PRIOR_TURN", phase="LOCAL_VALIDATION"
            )
        if not revision and self._turn_count != 0:
            raise OfficialCodexProviderError(
                "FRESH_THREAD_INITIAL_TURN_ALREADY_USED", phase="LOCAL_VALIDATION"
            )
        self._seen_attempt_keys.add(attempt_key)
        self._ensure_thread(developer_instructions)
        started = time.perf_counter()
        result: Any = None
        model_turn_completed = False
        try:
            result = self._thread.run(
                prompt,
                approval_mode=self._approval_mode.deny_all,
                effort=getattr(self._reasoning_effort, EFFORT),
                model=MODEL,
                output_schema=TRANSPORT_SCHEMA,
                sandbox=self._sandbox.read_only,
            )
        except TimeoutError as exc:
            raise OfficialCodexProviderError(
                "CODEX_TURN_TIMEOUT", phase="TIMEOUT"
            ) from exc
        except Exception as exc:
            kind = type(exc).__name__.lower()
            message = str(exc).lower()
            phase = "TURN_EXECUTION"
            if "rate" in kind or "rate" in message or "quota" in message:
                phase = "RATE_LIMIT"
            elif "context" in message and ("limit" in message or "length" in message):
                phase = "CONTEXT_LIMIT"
            elif "transport" in kind or "connection" in kind or "brokenpipe" in kind:
                phase = "APP_SERVER_TRANSPORT"
            raise OfficialCodexProviderError(
                f"CODEX_{phase}_FAILED", phase=phase
            ) from exc
        duration_ms = int(
            getattr(result, "duration_ms", None)
            or round((time.perf_counter() - started) * 1000)
        )
        status = str(_enum_value(getattr(result, "status", ""))).lower()
        if status != "completed" or getattr(result, "error", None) is not None:
            raise OfficialCodexProviderError(
                "CODEX_TURN_NOT_COMPLETED", phase="TURN_EXECUTION"
            )
        model_turn_completed = True
        content = getattr(result, "final_response", None)
        if not isinstance(content, str):
            raise OfficialCodexProviderError(
                "CODEX_FINAL_RESPONSE_MISSING",
                phase="STRUCTURED_OUTPUT",
                model_turn_completed=True,
            )
        try:
            envelope = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OfficialCodexProviderError(
                "CODEX_FINAL_RESPONSE_NOT_JSON",
                phase="STRUCTURED_OUTPUT",
                model_turn_completed=True,
            ) from exc
        if (
            not isinstance(envelope, dict)
            or set(envelope) != {"article_json"}
            or not isinstance(envelope.get("article_json"), str)
        ):
            raise OfficialCodexProviderError(
                "CODEX_STRICT_TRANSPORT_SCHEMA_INVALID",
                phase="STRUCTURED_OUTPUT",
                model_turn_completed=True,
            )
        try:
            output = json.loads(envelope["article_json"])
        except json.JSONDecodeError as exc:
            raise OfficialCodexProviderError(
                "CODEX_ARTICLE_JSON_INVALID",
                phase="TURN_RESULT_NORMALIZATION",
                model_turn_completed=True,
            ) from exc
        if not isinstance(output, dict):
            raise OfficialCodexProviderError(
                "CODEX_ARTICLE_OUTPUT_NOT_OBJECT",
                phase="TURN_RESULT_NORMALIZATION",
                model_turn_completed=True,
            )
        item_types = [_item_type(item) for item in getattr(result, "items", ())]
        forbidden = (
            "command",
            "file_change",
            "mcp",
            "shell",
            "tool",
            "web",
            "computer",
        )
        if any(marker in item.lower() for item in item_types for marker in forbidden):
            raise OfficialCodexProviderError(
                "CODEX_UNEXPECTED_ACTION_ITEM",
                phase="LOCAL_VALIDATION",
                model_turn_completed=True,
            )
        if any(self.proof_cwd.iterdir()):
            raise OfficialCodexProviderError(
                "CODEX_READ_ONLY_CWD_MUTATED",
                phase="LOCAL_VALIDATION",
                model_turn_completed=True,
            )
        metadata_status = "NOT_ATTEMPTED"
        runtime_version = "UNKNOWN"
        try:
            # Metadata only. TurnResult above is the response/usage/status/timing authority.
            readback = self._thread.read(include_turns=False).thread
            runtime_version = str(getattr(readback, "cli_version", "UNKNOWN"))
            metadata_status = (
                "PASS_EPHEMERAL"
                if getattr(readback, "ephemeral", None) is True
                else "READBACK_EPHEMERAL_STATE_UNCONFIRMED"
            )
        except Exception:
            # A completed model turn remains completed; metadata failure is a separate phase.
            metadata_status = "FAILED_POST_TURN_METADATA_READBACK"
        usage = _usage(getattr(result, "usage", None))
        receipt = {
            "schema_version": "contentops.official_codex_turn_receipt.v1",
            "provider": PROVIDER_ID,
            "transport": TRANSPORT,
            "sdk_version": self._sdk_version,
            "runtime_version": runtime_version,
            "auth_classification": AUTH_CLASSIFICATION,
            "api_key_fallback_calls": 0,
            "model": MODEL,
            "reasoning_effort": EFFORT.upper(),
            "thread_ephemeral": True,
            "sandbox": "read_only",
            "approval_mode": "deny_all",
            "thread_id_hash": self._thread_id_hash,
            "same_thread_revision": bool(revision),
            "turn_index": self._turn_count,
            "attempt_key": attempt_key,
            "governed_input_hash": governed_input_hash,
            "evidence_hash": evidence_hash,
            "prompt_utf8_bytes": len(prompt.encode("utf-8")),
            "prompt_sha256": _sha256(prompt),
            "developer_instruction_utf8_bytes": len(
                developer_instructions.encode("utf-8")
            ),
            "developer_instruction_sha256": _sha256(developer_instructions),
            "transport_schema_sha256": _sha256(TRANSPORT_SCHEMA),
            "turn_result_status": status,
            "turn_result_final_response_sha256": _sha256(content),
            "turn_result_item_types": item_types,
            "turn_result_usage": usage,
            "turn_result_duration_ms": duration_ms,
            "structured_output_sha256": _sha256(envelope),
            "normalized_article_sha256": _sha256(output),
            "completed_phase": "LOCAL_VALIDATION",
            "post_turn_metadata_phase": "POST_TURN_METADATA_READBACK",
            "post_turn_metadata_status": metadata_status,
            "model_turn_completed": model_turn_completed,
            "turn_result_is_primary_authority": True,
            "thread_read_include_turns": False,
            "gemini_formatter_calls": 0,
            "public_write_attempted": False,
        }
        self._turn_count += 1
        return OfficialCodexTurnExecution(output=output, receipt=receipt)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._sdk_context is not None:
            self._sdk_context.__exit__(None, None, None)
        self._codex = None
        self._thread = None


class OfficialCodexEditorialArticleBuilder:
    """Callable adapter from the existing editorial route to the existing article builder."""

    DEVELOPER_INSTRUCTIONS = (
        "You are the isolated Capital Chronicle editorial writer. Use only the governed evidence "
        "and exact source markers in the user prompt. You have no factual, numeric, permission, "
        "Capital Chronicle analytical, publication, or public-write authority. Do not use tools, "
        "commands, files, web browsing, or external knowledge. Return the complete requested "
        "article object serialized as JSON in the article_json string."
    )

    def __init__(
        self,
        *,
        output_dir: Path,
        sdk_factory: Callable[[], Any] | None = None,
        environment: Mapping[str, str] | None = None,
        required_title: str | None = None,
    ) -> None:
        self.output_dir = Path(output_dir).resolve()
        self.session = OfficialCodexEditorialSession(
            proof_cwd=self.output_dir / "official_codex_read_only_cwd",
            sdk_factory=sdk_factory,
            environment=environment,
        )
        self._initial_worker_receipt: dict[str, Any] | None = None
        self.required_title = " ".join(str(required_title or "").split()) or None

    def __enter__(self) -> "OfficialCodexEditorialArticleBuilder":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        del exc_type, exc, traceback
        self.close()

    @staticmethod
    def _request(viability: Mapping[str, Any]) -> dict[str, Any]:
        request = dict(viability.get("editorial_worker_request") or {})
        if (
            request.get("model") != MODEL
            or str(request.get("reasoning_effort") or "").lower() != EFFORT
            or request.get("fresh") is not True
            or request.get("isolated") is not True
        ):
            raise OfficialCodexProviderError(
                "EDITORIAL_WORKER_REQUEST_INVALID", phase="LOCAL_VALIDATION"
            )
        return request

    @staticmethod
    def _evidence_hash(request: Mapping[str, Any]) -> str:
        packet = dict(
            (request.get("bounded_governed_context") or {}).get(
                "accepted_evidence_packet"
            )
            or {}
        )
        return _sha256(packet)

    @staticmethod
    def _article_hash(article: Mapping[str, Any]) -> str:
        return _sha256(dict(article))

    def _build(
        self,
        viability: Mapping[str, Any],
        *,
        revision_contract: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
            build_rolling_x_grounded_article_and_media,
        )

        request = self._request(viability)
        governed_hash = str(request.get("governed_input_hash") or "")
        if not governed_hash:
            raise OfficialCodexProviderError(
                "EDITORIAL_GOVERNED_INPUT_HASH_REQUIRED", phase="LOCAL_VALIDATION"
            )
        execution: OfficialCodexTurnExecution | None = None
        raw_article: dict[str, Any] | None = None

        def generator(prompt: str) -> Mapping[str, Any]:
            nonlocal execution, raw_article
            effective_prompt = prompt
            revision = revision_contract is not None
            if self.required_title:
                effective_prompt += (
                    "\n\nOWNER-AUTHORIZED EDITORIAL TITLE CONSTRAINT: Return "
                    "canonical_editorial_headline and title exactly as: "
                    + json.dumps(self.required_title)
                    + ". This changes no factual scope or authority."
                )
            if revision:
                effective_prompt += (
                    "\n\nSAME_WORKER_REVISION_CONTRACT:\n"
                    + _canonical_json(dict(revision_contract or {}))
                )
                effective_prompt += (
                    "\nRevise your prior article in this same thread. Address only the supplied "
                    "bounded blocker codes, preserve evidence scope, and return the entire article."
                )
            execution = self.session.run(
                prompt=effective_prompt,
                developer_instructions=self.DEVELOPER_INSTRUCTIONS,
                governed_input_hash=governed_hash,
                evidence_hash=self._evidence_hash(request),
                role="V1_FINAL_EDITORIAL_REVISION"
                if revision
                else "V1_FINAL_EDITORIAL_WRITER",
                revision=revision,
            )
            raw_article = dict(execution.output)
            # Persist only the secret-free normalized TurnResult receipt. This happens before
            # product validation so a completed turn remains auditable even if local validation
            # rejects the article. Raw model output is retained only in memory.
            receipt_path = self.output_dir / (
                "official_codex_turn_receipt_revision_1_v1.json"
                if revision
                else "official_codex_turn_receipt_v1.json"
            )
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(
                json.dumps(
                    dict(execution.receipt),
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            return raw_article

        try:
            built = build_rolling_x_grounded_article_and_media(
                viability,
                output_dir=self.output_dir,
                article_generator=generator,
            )
        except Exception as exc:
            from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
                GroundedArticleBuilderError,
            )

            if (
                revision_contract is None
                and isinstance(exc, GroundedArticleBuilderError)
                and execution is not None
                and raw_article is not None
            ):
                # Product validation is deterministic authority. Give the same in-memory thread
                # its sole bounded repair opportunity; never create a replacement thread or use
                # another model as a formatter.
                local_contract = {
                    "schema_version": "contentops.same_xhigh_local_validation_revision.v1",
                    "decision": "SAME_XHIGH_WORKER_REVISION_REQUIRED",
                    "same_worker_required": True,
                    "fresh_replacement_worker_forbidden": True,
                    "required_bounded_revision_count": 1,
                    "maximum_bounded_revision_count": 1,
                    "prior_worker_return_hash": _sha256(raw_article),
                    "deterministic_blockers": [
                        value for value in str(exc).split(";") if value
                    ],
                    "governed_input_hash": governed_hash,
                    "public_write_authority": False,
                    "publication_authority": False,
                }
                return self._build(
                    viability,
                    revision_contract=local_contract,
                )
            raise
        if execution is None or raw_article is None:
            raise OfficialCodexProviderError(
                "EDITORIAL_TURN_RESULT_MISSING", phase="LOCAL_VALIDATION"
            )
        if (
            self.required_title
            and str((built.get("article") or {}).get("title") or "")
            != self.required_title
        ):
            raise OfficialCodexProviderError(
                "REQUIRED_EDITORIAL_TITLE_MISMATCH",
                phase="LOCAL_VALIDATION",
                model_turn_completed=True,
            )
        revision_count = int(
            (revision_contract or {}).get("required_bounded_revision_count") or 0
        )
        worker_receipt = {
            "schema_version": "contentops.official_codex_editorial_worker_return.v1",
            "governed_input_hash": governed_hash,
            "model": MODEL,
            "reasoning_effort": EFFORT.upper(),
            "fresh": True,
            "isolated": True,
            "bounded_revision_count": revision_count,
            "same_worker_revision_of_return_hash": (
                str((revision_contract or {}).get("prior_worker_return_hash") or "")
                or None
            ),
            "same_worker_local_validation_revision": bool(
                revision_contract
                and revision_contract.get("schema_version")
                == "contentops.same_xhigh_local_validation_revision.v1"
            ),
            "article": dict(built.get("article") or {}),
            "raw_model_article_sha256": self._article_hash(raw_article),
            "raw_worker_body_sha256": _sha256(
                str(raw_article.get("substack_body_markdown") or "")
            ),
            "resolved_public_body_sha256": _sha256(
                str((built.get("article") or {}).get("substack_body_markdown") or "")
            ),
            "official_codex_turn_receipt": dict(execution.receipt),
            "public_write_attempted": False,
            "publication_authority": False,
        }
        built = {
            **dict(built),
            "editorial_worker_receipt": worker_receipt,
            "critical_path_telemetry": {
                **dict(built.get("critical_path_telemetry") or {}),
                "article_writer_semantic_calls": 1 + revision_count,
                "official_codex_direct_provider_calls": 1 + revision_count,
                "same_thread_revision": revision_contract is not None,
                "api_key_fallback_calls": 0,
            },
        }
        if revision_contract is None:
            self._initial_worker_receipt = worker_receipt
        return built

    def __call__(self, viability: Mapping[str, Any]) -> dict[str, Any]:
        from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
            GroundedArticleBuilderError,
        )

        if self._initial_worker_receipt is not None:
            raise GroundedArticleBuilderError("NEXT_NATIVE_XHIGH_WORKER_REQUIRED")
        try:
            return self._build(viability)
        except OfficialCodexProviderError as exc:
            raise GroundedArticleBuilderError(
                f"OFFICIAL_CODEX_PROVIDER_{exc.phase}:{exc.code}"
            ) from exc

    def revise_same_worker(self, viability: Mapping[str, Any]) -> dict[str, Any]:
        from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
            GroundedArticleBuilderError,
        )

        contract = dict(viability.get("same_xhigh_worker_revision_contract") or {})
        if (
            self._initial_worker_receipt is None
            or contract.get("same_worker_required") is not True
            or contract.get("fresh_replacement_worker_forbidden") is not True
        ):
            raise GroundedArticleBuilderError("SAME_XHIGH_REVISION_CONTRACT_INVALID")
        try:
            return self._build(viability, revision_contract=contract)
        except OfficialCodexProviderError as exc:
            raise GroundedArticleBuilderError(
                f"OFFICIAL_CODEX_PROVIDER_{exc.phase}:{exc.code}"
            ) from exc

    def preflight(self) -> dict[str, Any]:
        return self.session.preflight()

    def close(self) -> None:
        self.session.close()
