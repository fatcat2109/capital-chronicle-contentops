"""Brain-neutral V2 creative boundary with NineRouterGPT56Brain active by default."""

from __future__ import annotations

import json
import base64
import hashlib
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_V2_CREATIVE_EDITOR,
    ROLE_V2_CREATIVE_REVISION_AUTHOR,
    ROLE_V2_MOTION_CODE_AUTHOR,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    ProviderResult,
    RetryBudget,
    V2_CREATIVE_CX_XHIGH_MODEL,
)
from live_contentops.nine_router_provider_adapter_v2 import (
    call_nine_router_v2_isolated,
    call_nine_router_v2_isolated_minimal_raw,
)
from live_contentops.retention_native_concrete_first_v2 import (
    CREATIVE_MODEL,
    CreativeBible,
    VisualGroundingContract,
    logical_hash,
    validate_segment_graph,
)
from live_contentops.v2_isolated_llm_execution_v1 import routed_v2_isolated_invocation

SCHEMA_VERSION = "contentops.retention_native.creative_brain.v2"
ACTIVE_BRAIN = "NineRouterGPT56Brain"


def _strip_trailing_commas(text: str) -> str:
    output: list[str] = []
    in_string = False
    escaped = False
    index = 0
    while index < len(text):
        character = text[index]
        if in_string:
            output.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
            output.append(character)
            index += 1
            continue
        if character == ",":
            lookahead = index + 1
            while lookahead < len(text) and text[lookahead].isspace():
                lookahead += 1
            if lookahead < len(text) and text[lookahead] in "}]":
                index += 1
                continue
        output.append(character)
        index += 1
    return "".join(output)


def deterministic_json_normalization(text: str) -> tuple[str, tuple[str, ...]]:
    """Normalize only mechanical JSON wrapping/syntax and report every operation."""
    candidate = str(text).strip()
    operations: list[str] = []
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[1] if "\n" in candidate else candidate
        candidate = re.sub(r"```\s*$", "", candidate).strip()
        operations.append("strip_markdown_json_fence")
    try:
        json.loads(candidate)
        return candidate, tuple(operations)
    except json.JSONDecodeError:
        pass

    without_trailing = _strip_trailing_commas(candidate)
    if without_trailing != candidate:
        candidate = without_trailing
        operations.append("strip_trailing_commas_outside_strings")
        try:
            json.loads(candidate)
            return candidate, tuple(operations)
        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", candidate):
        try:
            possible, consumed = decoder.raw_decode(candidate[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(possible, Mapping):
            span = candidate[match.start() : match.start() + consumed]
            if match.start() != 0 or candidate[match.start() + consumed :].strip():
                operations.append("extract_json_object_span")
            return span, tuple(operations)
    raise json.JSONDecodeError("deterministic_json_normalization_failed", candidate, 0)


def _extract_json(text: str) -> Mapping[str, Any]:
    candidate, _ = deterministic_json_normalization(text)
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        raise
    if not isinstance(value, Mapping):
        raise ValueError("creative_output_json_object_required")
    return value


def parse_director_output_with_telemetry(
    text: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized, operations = deterministic_json_normalization(text)
    row = json.loads(normalized)
    if not isinstance(row, Mapping):
        raise ValueError("creative_output_json_object_required")
    bible = CreativeBible.from_mapping(dict(row["creative_bible"]))
    graph = validate_segment_graph(list(row["segment_graph"]))
    payload = {
        "creative_bible": bible.freeze()["value"],
        "segment_graph": [segment.__dict__ for segment in graph],
    }
    raw_bytes = str(text).encode("utf-8")
    normalized_bytes = normalized.encode("utf-8")
    telemetry = {
        "route": "DIRECT_PARSE" if not operations else "DETERMINISTIC_REPAIR",
        "operations": list(operations),
        "raw_model_output_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "raw_model_output_byte_size": len(raw_bytes),
        "normalized_json_sha256": hashlib.sha256(normalized_bytes).hexdigest(),
        "normalized_json_byte_size": len(normalized_bytes),
        "semantic_payload_sha256": logical_hash(payload),
        "creative_meaning_changed": False,
    }
    return payload, telemetry


def validate_director_output(text: str) -> tuple[bool, str | None, Any, str | None]:
    try:
        payload, _ = parse_director_output_with_telemetry(text)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return (
            False,
            "structured_output_schema_invalid",
            None,
            f"director_{type(exc).__name__}",
        )
    return True, None, payload, None


def _validate_beat(row: Mapping[str, Any], expected_aspect: str) -> None:
    contract = VisualGroundingContract.from_mapping(row)
    if contract.aspect_ratio != expected_aspect:
        raise ValueError(f"segment_beat_aspect_mismatch:{contract.beat_id}")
    for key in (
        "narration",
        "storyboard_frame",
        "focal_object",
        "source_label",
        "asset_placement",
        "crop_anchor",
        "motion_intent",
        "transition_intent",
        "timing_easing",
        "audio_state",
    ):
        if not str(row.get(key) or "").strip():
            raise ValueError(f"segment_beat_missing:{contract.beat_id}:{key}")
    asset_ids = row.get("asset_ids")
    if not isinstance(asset_ids, list) or not asset_ids:
        raise ValueError(f"segment_beat_asset_ids_missing:{contract.beat_id}")
    if not set(contract.required_asset_ids) <= {str(item) for item in asset_ids}:
        raise ValueError(f"segment_beat_required_asset_not_selected:{contract.beat_id}")
    if row.get("audio_state") not in {
        "cold_open",
        "tension",
        "evidence",
        "mechanism",
        "consequence",
        "boundary",
        "resolution",
        "outro",
    }:
        raise ValueError(f"segment_beat_audio_state_invalid:{contract.beat_id}")
    if row.get("sfx_kind") not in {"none", "whoosh", "riser", "hit", "data_tick"}:
        raise ValueError(f"segment_beat_sfx_kind_invalid:{contract.beat_id}")
    fraction = float(row.get("sfx_at_fraction", 0))
    if not 0 <= fraction <= 1:
        raise ValueError(f"segment_beat_sfx_fraction_invalid:{contract.beat_id}")
    duration = float(row.get("duration_seconds") or 0)
    if duration <= 0 or duration > 20:
        raise ValueError(f"segment_beat_duration_invalid:{contract.beat_id}")


def validate_segment_output(text: str) -> tuple[bool, str | None, Any, str | None]:
    try:
        row = dict(_extract_json(text))
        if not str(row.get("segment_summary") or "").strip():
            raise ValueError("segment_summary_missing")
        for key, aspect in (
            ("short_9x16_beats", "9:16"),
            ("midform_16x9_beats", "16:9"),
        ):
            beats = row.get(key)
            if not isinstance(beats, list) or not beats:
                raise ValueError(f"{key}_missing")
            for beat in beats:
                if not isinstance(beat, Mapping):
                    raise ValueError(f"{key}_beat_invalid")
                _validate_beat(beat, aspect)
        if not isinstance(row.get("continuity_state_leaving"), list):
            raise ValueError("continuity_state_leaving_invalid")
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return (
            False,
            "structured_output_schema_invalid",
            None,
            f"segment_{type(exc).__name__}",
        )
    return True, None, row, None


def validate_motion_output(text: str) -> tuple[bool, str | None, Any, str | None]:
    try:
        row = dict(_extract_json(text))
        if not str(row.get("batch_id") or "").strip():
            raise ValueError("motion_batch_id_missing")
        files = row.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("motion_files_missing")
        for file in files:
            if not isinstance(file, Mapping):
                raise ValueError("motion_file_invalid")
            path = str(file.get("path") or "")
            source = str(file.get("source") or "")
            if not path.startswith("src/generated/") or not path.endswith(
                (".tsx", ".ts")
            ):
                raise ValueError("motion_file_path_outside_generated_root")
            if not source.strip():
                raise ValueError("motion_file_source_missing")
        beat_ids = row.get("beat_ids")
        if not isinstance(beat_ids, list) or not beat_ids:
            raise ValueError("motion_beat_ids_missing")
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return (
            False,
            "structured_output_schema_invalid",
            None,
            f"motion_{type(exc).__name__}",
        )
    return True, None, row, None


@dataclass(frozen=True)
class CreativeReceipt:
    role: str
    logical_invocation_id: str
    input_sha256: str
    requested_model: str
    effective_model: str | None
    output_sha256: str
    terminal_disposition: str
    attempts: tuple[Mapping[str, Any], ...]
    total_usage: Mapping[str, Any] | None
    total_cost: Mapping[str, Any] | None
    degraded_creative_model: bool
    professional_candidate_eligible: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "attempts": [dict(row) for row in self.attempts],
        }


class CreativeBrain:
    """Interface for bounded creative authorship.  Implementations return output + receipt."""

    def author(
        self,
        *,
        role: str,
        prompt_payload: Mapping[str, Any],
        validator: Callable[[str], tuple[bool, str | None, Any, str | None]],
        logical_invocation_id: str,
        prompt_template: str,
        prompt_version: str,
        image_paths: tuple[str, ...] = (),
        max_tokens: int = 12000,
        wire_mode: str = "configured",
        evidence_dir: Path | None = None,
        retry_budget: RetryBudget | None = None,
        model_pool_override: tuple[str, ...] | None = None,
        response_stream: bool | None = None,
    ) -> tuple[Mapping[str, Any], CreativeReceipt]:
        raise NotImplementedError


class NineRouterGPT56Brain(CreativeBrain):
    name = ACTIVE_BRAIN

    def author(
        self,
        *,
        role: str,
        prompt_payload: Mapping[str, Any],
        validator: Callable[[str], tuple[bool, str | None, Any, str | None]],
        logical_invocation_id: str,
        prompt_template: str,
        prompt_version: str,
        image_paths: tuple[str, ...] = (),
        max_tokens: int = 12000,
        wire_mode: str = "configured",
        evidence_dir: Path | None = None,
        retry_budget: RetryBudget | None = None,
        model_pool_override: tuple[str, ...] | None = None,
        response_stream: bool | None = None,
    ) -> tuple[Mapping[str, Any], CreativeReceipt]:
        if role not in {
            ROLE_V2_CREATIVE_EDITOR,
            ROLE_V2_MOTION_CODE_AUTHOR,
            ROLE_V2_CREATIVE_REVISION_AUTHOR,
        }:
            raise ValueError(f"creative_role_not_authorized:{role}")
        if wire_mode not in {"configured", "minimal_raw"}:
            raise ValueError(f"creative_wire_mode_not_authorized:{wire_mode}")
        if wire_mode == "minimal_raw" and evidence_dir is None:
            raise ValueError("minimal_raw_evidence_dir_required")
        prompt = json.dumps(prompt_payload, sort_keys=True, ensure_ascii=False)

        def provider(current_prompt: str, model: str, timeout: float) -> ProviderResult:
            provider_prompt: Any = current_prompt
            if image_paths:
                content: list[dict[str, Any]] = [
                    {"type": "text", "text": current_prompt}
                ]
                for raw_path in image_paths:
                    path = Path(raw_path)
                    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
                    uri = f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": uri, "detail": "high"},
                        }
                    )
                provider_prompt = content
            if wire_mode == "minimal_raw":
                return call_nine_router_v2_isolated_minimal_raw(
                    provider_prompt,
                    model,
                    timeout,
                    role_task_id=role,
                    logical_invocation_id=logical_invocation_id,
                    component=ACTIVE_BRAIN,
                    evidence_dir=Path(evidence_dir),
                    stream=response_stream,
                )
            return call_nine_router_v2_isolated(
                provider_prompt,
                model,
                timeout,
                role_task_id=role,
                logical_invocation_id=logical_invocation_id,
                component=ACTIVE_BRAIN,
                max_tokens=max_tokens,
                temperature=0.2,
            )

        invocation = routed_v2_isolated_invocation(
            prompt=prompt,
            role_task_id=role,
            logical_invocation_id=logical_invocation_id,
            component=ACTIVE_BRAIN,
            work_item_id=logical_hash(prompt_payload)[:32],
            timeout_seconds=600.0,
            validator=validator,
            provider_call=provider,
            governed_input=prompt_payload,
            prompt_template=prompt_template,
            prompt_version=prompt_version,
            budget=retry_budget,
            model_pool_override=model_pool_override,
        )
        if invocation.get("terminal_disposition") != ACCEPTED:
            raise RuntimeError(
                f"creative_router_blocked:{role}:{invocation.get('terminal_disposition')}"
            )
        output = invocation.get("output")
        if not isinstance(output, Mapping):
            raise RuntimeError("creative_router_accepted_non_object")
        effective = str(invocation.get("selected_model") or "") or None
        professional_models = {CREATIVE_MODEL, V2_CREATIVE_CX_XHIGH_MODEL}
        degraded = effective not in professional_models
        receipt = CreativeReceipt(
            role=role,
            logical_invocation_id=logical_invocation_id,
            input_sha256=logical_hash(prompt_payload),
            requested_model=(model_pool_override or (CREATIVE_MODEL,))[0],
            effective_model=effective,
            output_sha256=logical_hash(output),
            terminal_disposition=str(invocation["terminal_disposition"]),
            attempts=tuple(invocation.get("attempts") or ()),
            total_usage=invocation.get("total_usage"),
            total_cost=invocation.get("total_cost"),
            degraded_creative_model=degraded,
            professional_candidate_eligible=not degraded,
        )
        return dict(output), receipt


class CodexLocalBrain(CreativeBrain):
    """Defined for a future owner decision; intentionally impossible to activate here."""

    name = "CodexLocalBrain"
    active = False

    def author(self, **_: Any) -> tuple[Mapping[str, Any], CreativeReceipt]:
        raise RuntimeError("CODEX_LOCAL_BRAIN_INERT_OWNER_AUTHORIZATION_REQUIRED")


def active_brain() -> CreativeBrain:
    return NineRouterGPT56Brain()
