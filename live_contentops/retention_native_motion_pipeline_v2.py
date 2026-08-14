"""Post-comprehension motion authorship, render, audio, and media QA for V2-01."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.media_manifest_authority_v1 import sha256_file
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_V2_CREATIVE_REVISION_AUTHOR,
    ROLE_V2_MOTION_CODE_AUTHOR,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    RetryBudget,
    V2_CREATIVE_CX_XHIGH_MODEL,
)
from live_contentops.retention_native_audio_score_v2 import render_owned_score
from live_contentops.retention_native_concrete_first_v2 import (
    canonical_json,
    logical_hash,
)
from live_contentops.retention_native_creative_brain_v2 import (
    CreativeReceipt,
    NineRouterGPT56Brain,
    validate_motion_output,
)
from live_contentops.retention_native_motion_sandbox_v2 import (
    persist_authored_files,
    validate_generated_motion_files,
)
from live_contentops.retention_native_replacement_runner_v2 import (
    DEFAULT_RUNTIME,
    VIDEO_ID,
)

SCHEMA_VERSION = "contentops.retention_native.motion_pipeline.v2"
RENDERER_RELATIVE = Path("video") / "concrete_first_v2"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8")


def _runtime_video_id(runtime: Path) -> str:
    manifest_path = runtime / "motion_render_manifest_v2.json"
    if manifest_path.is_file():
        value = str(_read_json(manifest_path).get("video_id") or "").strip()
        if value:
            return value
    return VIDEO_ID


def _run(
    command: Sequence[str], *, cwd: Path | None = None, timeout: float = 3600
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"command_failed:{Path(command[0]).name}:{result.stderr[-2000:]}:{result.stdout[-1000:]}"
        )
    return result


def _safe(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")
    if not cleaned:
        raise ValueError("generated_identifier_empty")
    return cleaned


def _composition_id(variant: str, segment_id: str) -> str:
    """Return a Remotion-valid stable registry ID (underscores are forbidden)."""
    return "Seg-" + re.sub(r"[^a-zA-Z0-9-]+", "-", f"{variant}-{segment_id}")


MOTION_INSTRUCTION = """You are the exact XHIGH Motion Code Author. The storyboard and visual-grounding decisions are already accepted; implement them faithfully as deterministic React/Remotion code. Author only the supplied segment/variant, small enough for one bounded response. Return ONLY JSON: {batch_id,beat_ids,files:[{path,source}]}. Produce exactly one TSX file at the required_path and export the required_component_name React.FC<VariantProps>. Import VariantProps from '../types'. Use only React and approved Remotion APIs (AbsoluteFill, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig). No network, env, filesystem, shell, dynamic dependencies, randomness, CSS transitions, or publication actions. Every exact beat_id must appear literally in source. Use the exact asset relative_public_path bindings; required real assets may not be replaced with geometry. Use frame-driven cuts, reframes, document punch-ins, map progression, native data comparisons, annotations, and purposeful holds exactly as storyboard intent warrants. Captions render only when captionsVisible is true; source labels and editorial labels remain. Keep source labels readable, prevent overflow, preserve safe zones. Avoid generic cards, unexplained symbols, universal zoom/parallax, repeated easing/direction, chart crawl, and unrelated simultaneous motion. The component starts at its own local frame zero and lasts exact duration_frames."""


def _normalize_motion_batch_identity(
    output: Mapping[str, Any], *, variant: str, segment_id: str
) -> tuple[dict[str, Any], str | None]:
    """Normalize the one semantically equivalent qualified batch identifier."""
    normalized = dict(output)
    expected = f"{variant}:{segment_id}"
    actual = str(normalized.get("batch_id") or "")
    qualified = f"{VIDEO_ID}:{segment_id}:{variant}"
    filesystem_style = f"{variant}_{segment_id}"
    reversed_filesystem_style = f"{segment_id}_{variant}"
    qualified_filesystem_style = f"{VIDEO_ID}_{variant}_{segment_id}"
    qualified_double_underscore_style = f"{VIDEO_ID}__{segment_id}__{variant}"
    qualified_short_style = f"{VIDEO_ID}-{variant}-{segment_id.split('_', 1)[0]}"
    reversed_hyphen_xhigh_style = f"{segment_id}-{variant}-xhigh"
    hashed_reversed_style = re.fullmatch(
        re.escape(f"{segment_id}_{variant}_") + r"(?:[0-9a-fA-F]{4,16}|xhigh)",
        actual,
    )
    if actual == expected:
        return normalized, None
    if (
        actual
        not in {
            qualified,
            filesystem_style,
            reversed_filesystem_style,
            qualified_filesystem_style,
            qualified_double_underscore_style,
            qualified_short_style,
            reversed_hyphen_xhigh_style,
        }
        and hashed_reversed_style is None
    ):
        raise RuntimeError(f"motion_batch_identity_mismatch:{variant}:{segment_id}")
    normalized["batch_id"] = expected
    return normalized, actual


def author_motion(
    *, runtime: Path, repo_root: Path, only_batch: str | None = None
) -> dict[str, Any]:
    premotion = _read_json(runtime / "premotion_comprehension_report_v2.json")
    if premotion["deterministic_gate"]["motion_code_authorized"] is not True:
        raise RuntimeError("motion_author_called_before_comprehension_pass")
    director = _read_json(runtime / "contracts" / "creative_director_v2.json")
    segments = _read_json(runtime / "contracts" / "segment_authorship_v2.json")
    storyboard = _read_json(runtime / "storyboard_animatic_manifest_v2.json")
    assets = _read_json(runtime / "contracts" / "asset_candidate_universe_v2.json")
    renderer_root = (repo_root / RENDERER_RELATIVE).resolve()
    asset_bindings = {
        row["asset_id"]: {
            "relative_public_path": row["relative_public_path"],
            "rights_status": row["rights_status"],
            "attribution": row["attribution"],
            "recognizable_focal_object": row["recognizable_focal_object"],
        }
        for row in assets["candidates"]
    }
    authored: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    expected_batch_ids: list[str] = []
    for variant in ("short_9x16", "midform_16x9"):
        variant_beats = segments[f"{variant}_beats"]
        frame_rows = {
            row["beat_id"]: row for row in storyboard["variants"][variant]["frames"]
        }
        for segment in segments["segments"]:
            key = f"{variant}_beats"
            beats = list(segment[key])
            segment_id = str(segment["segment_id"])
            batch_id = f"{variant}:{segment_id}"
            expected_batch_ids.append(batch_id)
            safe_variant = _safe(variant)
            safe_segment = _safe(segment_id)
            batch_manifest_path = (
                runtime
                / "contracts"
                / "motion_batches"
                / f"{safe_variant}_{safe_segment}.json"
            )
            batch_receipt_path = (
                runtime / "receipts" / "motion" / f"{safe_variant}_{safe_segment}.json"
            )
            if batch_manifest_path.is_file() and batch_receipt_path.is_file():
                existing_batch = _read_json(batch_manifest_path)
                existing_batch["composition_id"] = _composition_id(
                    str(existing_batch["variant_id"]),
                    str(existing_batch["segment_id"]),
                )
                _write_json(batch_manifest_path, existing_batch)
                authored.append(existing_batch)
                receipts.append(_read_json(batch_receipt_path))
                continue
            if only_batch is not None and batch_id != only_batch:
                continue
            component_name = f"Motion_{safe_variant}_{safe_segment}"
            required_path = f"src/generated/{safe_variant}_{safe_segment}.tsx"
            duration_frames = int(
                round(sum(float(beat["duration_seconds"]) for beat in beats) * 30)
            )
            selected_asset_ids = {
                str(asset_id) for beat in beats for asset_id in beat["asset_ids"]
            }
            prompt = {
                "instruction": MOTION_INSTRUCTION,
                "video_id": VIDEO_ID,
                "variant_id": variant,
                "dimensions": {
                    "width": 1080 if variant == "short_9x16" else 1920,
                    "height": 1920 if variant == "short_9x16" else 1080,
                    "fps": 30,
                },
                "required_path": required_path,
                "required_component_name": component_name,
                "duration_frames": duration_frames,
                "immutable_creative_bible": director["creative_bible"],
                "segment_contract": next(
                    row
                    for row in director["segment_graph"]
                    if row["segment_id"] == segment_id
                ),
                "accepted_segment_artifact": segment,
                "accepted_beats": beats,
                "accepted_storyboard_frames": [
                    frame_rows[beat["beat_id"]] for beat in beats
                ],
                "resolved_assets": {
                    asset_id: asset_bindings[asset_id]
                    for asset_id in selected_asset_ids
                },
                "neighboring_context": {
                    "previous_beat_id": variant_beats[
                        max(0, variant_beats.index(beats[0]) - 1)
                    ]["beat_id"]
                    if variant_beats.index(beats[0]) > 0
                    else None,
                    "next_beat_id": variant_beats[variant_beats.index(beats[-1]) + 1][
                        "beat_id"
                    ]
                    if variant_beats.index(beats[-1]) + 1 < len(variant_beats)
                    else None,
                },
                "technical_baseline": {
                    "remotion": "4.0.507",
                    "frame_driven": True,
                    "caption_safe_zone_bottom": 0.16
                    if variant == "short_9x16"
                    else 0.11,
                    "render_time_network": False,
                },
                "public_write_authority": False,
            }
            image_paths = tuple(frame_rows[beat["beat_id"]]["path"] for beat in beats)
            logical_invocation_id = (
                f"inv_v2_motion_{safe_variant}_{safe_segment}_"
                f"{logical_hash(prompt)[:14]}"
            )
            evidence_dir = (
                runtime / "provider_evidence" / "motion" / safe_variant / safe_segment
            )
            existing_raw = evidence_dir / "raw_model_output.txt"
            if existing_raw.is_file():
                raw_text = existing_raw.read_text(encoding="utf-8")
                valid, _, parsed, detail = validate_motion_output(raw_text)
                if not valid or not isinstance(parsed, Mapping):
                    raise RuntimeError(
                        f"existing_motion_output_invalid:{batch_id}:{detail}"
                    )
                output = dict(parsed)
                provider_receipt = _read_json(
                    evidence_dir / "minimal_raw_provider_receipt_v1.json"
                )
                receipt = CreativeReceipt(
                    role=ROLE_V2_MOTION_CODE_AUTHOR,
                    logical_invocation_id=logical_invocation_id,
                    input_sha256=logical_hash(prompt),
                    requested_model=V2_CREATIVE_CX_XHIGH_MODEL,
                    effective_model=V2_CREATIVE_CX_XHIGH_MODEL,
                    output_sha256=logical_hash(output),
                    terminal_disposition="ACCEPTED_REPLAY_FROM_RAW_PROVIDER_EVIDENCE",
                    attempts=(),
                    total_usage=provider_receipt.get("usage"),
                    total_cost=provider_receipt.get("cost"),
                    degraded_creative_model=False,
                    professional_candidate_eligible=True,
                )
            else:
                output, receipt = NineRouterGPT56Brain().author(
                    role=ROLE_V2_MOTION_CODE_AUTHOR,
                    prompt_payload=prompt,
                    validator=validate_motion_output,
                    logical_invocation_id=logical_invocation_id,
                    prompt_template="concrete_first_xhigh_motion_segment",
                    prompt_version="v2_minimal_raw_no_generation_config",
                    image_paths=image_paths,
                    wire_mode="minimal_raw",
                    evidence_dir=evidence_dir,
                    retry_budget=RetryBudget(
                        logical_invocation_id=logical_invocation_id,
                        max_total_provider_attempts=1,
                        max_fallback_transitions=0,
                        max_same_model_retries=0,
                        max_structured_output_repair_attempts=0,
                        max_cumulative_retry_sleep_seconds=0,
                        wall_clock_budget_seconds=600,
                        per_model_max_attempts=(1,),
                    ),
                    model_pool_override=(V2_CREATIVE_CX_XHIGH_MODEL,),
                    response_stream=True,
                )
            output, projected_from = _normalize_motion_batch_identity(
                output, variant=variant, segment_id=segment_id
            )
            if projected_from is not None:
                receipt = CreativeReceipt(
                    **(
                        receipt.__dict__
                        | {
                            "output_sha256": logical_hash(output),
                            "terminal_disposition": (
                                "ACCEPTED_AFTER_DETERMINISTIC_BATCH_ID_PROJECTION"
                            ),
                        }
                    )
                )
                _write_json(
                    evidence_dir / "deterministic_batch_id_projection_v1.json",
                    {
                        "schema_version": (
                            "contentops.v2.motion_batch_id_projection.v1"
                        ),
                        "from": projected_from,
                        "to": batch_id,
                        "creative_meaning_changed": False,
                        "model_call_used": False,
                        "public_write": False,
                    },
                )
            if output.get("beat_ids") != [beat["beat_id"] for beat in beats]:
                raise RuntimeError(
                    f"motion_beat_identity_mismatch:{variant}:{segment_id}"
                )
            files = list(output["files"])
            if len(files) != 1 or files[0].get("path") != required_path:
                raise RuntimeError(
                    f"motion_file_contract_mismatch:{variant}:{segment_id}"
                )
            sandbox = validate_generated_motion_files(
                files, expected_beat_ids=[beat["beat_id"] for beat in beats]
            )
            if sandbox["status"] != "PASS":
                raise RuntimeError(
                    f"motion_sandbox_block:{variant}:{segment_id}:{sandbox['violations']}"
                )
            provenance = persist_authored_files(files, renderer_root=renderer_root)
            receipt_row = receipt.to_dict()
            if receipt_row["degraded_creative_model"]:
                raise RuntimeError(
                    "professional_motion_candidate_degraded_creative_model"
                )
            row = {
                "variant_id": variant,
                "segment_id": segment_id,
                "component_name": component_name,
                "required_path": required_path,
                "duration_frames": duration_frames,
                "composition_id": _composition_id(variant, segment_id),
                "beat_ids": output["beat_ids"],
                "sandbox": sandbox,
                "provenance": provenance,
                "model_output_sha256": logical_hash(output),
                "receipt_sha256": logical_hash(receipt_row),
            }
            authored.append(row)
            receipts.append(receipt_row)
            _write_json(batch_manifest_path, row)
            _write_json(batch_receipt_path, receipt_row)
    completed_batch_ids = {
        f"{row['variant_id']}:{row['segment_id']}" for row in authored
    }
    missing_batch_ids = [
        batch_id
        for batch_id in expected_batch_ids
        if batch_id not in completed_batch_ids
    ]
    if missing_batch_ids:
        partial = {
            "schema_version": SCHEMA_VERSION,
            "status": "PARTIAL_CX_MOTION_AUTHORSHIP",
            "video_id": VIDEO_ID,
            "completed_batch_ids": sorted(completed_batch_ids),
            "missing_batch_ids": missing_batch_ids,
            "requested_batch_id": only_batch,
            "degraded_creative_model": False,
            "provenance_broken": False,
            "public_write": False,
        }
        _write_json(runtime / "motion_authorship_progress_v2.json", partial)
        return partial
    index = _mechanical_index(authored)
    index_path = renderer_root / "src" / "generated" / "index.tsx"
    before_placeholder = index_path.read_text(encoding="utf-8")
    index_path.write_text(index, encoding="utf-8", newline="\n")
    index_provenance = {
        "path": str(index_path),
        "before_sha256": logical_hash(before_placeholder),
        "after_sha256": logical_hash(index),
        "kind": "MECHANICAL_IMPORT_SEQUENCE_ASSEMBLY",
        "creative_inputs": [row["model_output_sha256"] for row in authored],
        "viewer_visible_creative_decisions_added_by_codex": False,
    }
    typecheck_command = (
        [str(renderer_root / "node_modules" / ".bin" / "tsc.cmd"), "--noEmit"]
        if (renderer_root / "node_modules" / ".bin" / "tsc.cmd").is_file()
        else ["npm", "run", "typecheck"]
    )
    typecheck = _run(typecheck_command, cwd=renderer_root, timeout=600)
    manifest = {
        "schema_version": "contentops.retention_native.motion_authorship.v2",
        "video_id": VIDEO_ID,
        "authored_batches": authored,
        "receipts": receipts,
        "index_provenance": index_provenance,
        "typecheck": {"status": "PASS", "stdout": typecheck.stdout[-2000:]},
        "degraded_creative_model": False,
        "provenance_broken": False,
        "public_write": False,
    }
    _write_json(runtime / "motion_authorship_manifest_v2.json", manifest)
    return manifest


LOCALIZED_REVISION_INSTRUCTION = """You are the exact CX XHIGH localized motion revision author. Revise only the two supplied S3 Remotion components to fix the independent critic's three localized presentation defects. Preserve every other factual, visual, timing, asset, narration-caption, source-label, and creative decision. Return ONLY JSON: {batch_id:'localized:S3_THE_FORECAST_ON_RECORD',beat_ids:[all exact supplied beat IDs in order],files:[{path,source},{path,source}]}. Return the two exact required paths. Keep the same exported component names and total local durations. The yellow document annotation must no longer obscure source excerpt words in S3_SHORT_01 or S3_MID_02. The S3_MID_04 chart crop must show the full June and 2027 forecast axis labels. Use only the existing allowed React/Remotion APIs and assets; no network, env, filesystem, shell, dependencies, randomness, or publication actions. Do not redesign unrelated beats."""


def revise_localized_s3(*, runtime: Path, repo_root: Path) -> dict[str, Any]:
    motion_path = runtime / "motion_authorship_manifest_v2.json"
    motion = _read_json(motion_path)
    critic = _read_json(runtime / "independent_critic_report_v2.json")
    material = [
        row
        for row in critic.get("issues") or []
        if row.get("segment_id") == "S3_THE_FORECAST_ON_RECORD"
    ]
    if critic.get("status") != "REVISE" or len(material) != 3:
        raise RuntimeError("localized_s3_revision_requires_exact_critic_block")
    renderer_root = (repo_root / RENDERER_RELATIVE).resolve()
    selected = [
        row
        for row in motion["authored_batches"]
        if row["segment_id"] == "S3_THE_FORECAST_ON_RECORD"
    ]
    if len(selected) != 2:
        raise RuntimeError("localized_s3_revision_batch_set_invalid")
    files = []
    beat_ids: list[str] = []
    for row in selected:
        path = renderer_root / Path(str(row["required_path"]))
        files.append(
            {
                "path": row["required_path"],
                "component_name": row["component_name"],
                "duration_frames": row["duration_frames"],
                "source": path.read_text(encoding="utf-8"),
            }
        )
        beat_ids.extend(row["beat_ids"])
    prompt = {
        "instruction": LOCALIZED_REVISION_INSTRUCTION,
        "video_id": VIDEO_ID,
        "critic_issues": material,
        "required_beat_ids": beat_ids,
        "existing_files": files,
        "public_write_authority": False,
    }
    logical_invocation_id = f"inv_v2_revision_s3_{logical_hash(prompt)[:18]}"
    evidence_dir = runtime / "provider_evidence" / "revision" / "S3"
    existing_raw = evidence_dir / "raw_model_output.txt"
    if existing_raw.is_file():
        valid, _, parsed, detail = validate_motion_output(
            existing_raw.read_text(encoding="utf-8")
        )
        if not valid or not isinstance(parsed, Mapping):
            raise RuntimeError(f"existing_revision_output_invalid:{detail}")
        output = dict(parsed)
        provider_receipt = _read_json(
            evidence_dir / "minimal_raw_provider_receipt_v1.json"
        )
        receipt = CreativeReceipt(
            role=ROLE_V2_CREATIVE_REVISION_AUTHOR,
            logical_invocation_id=logical_invocation_id,
            input_sha256=logical_hash(prompt),
            requested_model=V2_CREATIVE_CX_XHIGH_MODEL,
            effective_model=V2_CREATIVE_CX_XHIGH_MODEL,
            output_sha256=logical_hash(output),
            terminal_disposition="ACCEPTED_REPLAY_FROM_RAW_PROVIDER_EVIDENCE",
            attempts=(),
            total_usage=provider_receipt.get("usage"),
            total_cost=provider_receipt.get("cost"),
            degraded_creative_model=False,
            professional_candidate_eligible=True,
        )
    else:
        output, receipt = NineRouterGPT56Brain().author(
            role=ROLE_V2_CREATIVE_REVISION_AUTHOR,
            prompt_payload=prompt,
            validator=validate_motion_output,
            logical_invocation_id=logical_invocation_id,
            prompt_template="concrete_first_localized_s3_revision",
            prompt_version="v1_minimal_raw",
            wire_mode="minimal_raw",
            evidence_dir=evidence_dir,
            retry_budget=RetryBudget(
                logical_invocation_id=logical_invocation_id,
                max_total_provider_attempts=1,
                max_fallback_transitions=0,
                max_same_model_retries=0,
                max_structured_output_repair_attempts=0,
                max_cumulative_retry_sleep_seconds=0,
                wall_clock_budget_seconds=600,
                per_model_max_attempts=(1,),
            ),
            model_pool_override=(V2_CREATIVE_CX_XHIGH_MODEL,),
            response_stream=True,
        )
    if output.get("beat_ids") != beat_ids:
        raise RuntimeError("localized_s3_revision_beat_identity_mismatch")
    revised_files = list(output.get("files") or [])
    required_paths = {str(row["required_path"]) for row in selected}
    if {str(row.get("path") or "") for row in revised_files} != required_paths:
        raise RuntimeError("localized_s3_revision_file_set_mismatch")
    sandbox = validate_generated_motion_files(revised_files, expected_beat_ids=beat_ids)
    if sandbox["status"] != "PASS":
        raise RuntimeError(
            f"localized_s3_revision_sandbox_block:{sandbox['violations']}"
        )
    provenance = persist_authored_files(revised_files, renderer_root=renderer_root)
    receipt_row = receipt.to_dict()
    source_by_path = {str(row["path"]): str(row["source"]) for row in revised_files}
    for row in selected:
        row["model_output_sha256"] = logical_hash(
            source_by_path[str(row["required_path"])]
        )
        row["receipt_sha256"] = logical_hash(receipt_row)
        row["sandbox"] = sandbox
        row["provenance"] = provenance
        row["localized_revision"] = {
            "kind": "RENDERED_LOCALIZED",
            "critic_report_sha256": logical_hash(critic),
            "effective_model": V2_CREATIVE_CX_XHIGH_MODEL,
            "receipt_sha256": logical_hash(receipt_row),
        }
        _write_json(
            runtime
            / "contracts"
            / "motion_batches"
            / f"{_safe(row['variant_id'])}_{_safe(row['segment_id'])}.json",
            row,
        )
    typecheck_command = (
        [str(renderer_root / "node_modules" / ".bin" / "tsc.cmd"), "--noEmit"]
        if (renderer_root / "node_modules" / ".bin" / "tsc.cmd").is_file()
        else ["npm", "run", "typecheck"]
    )
    typecheck = _run(typecheck_command, cwd=renderer_root, timeout=600)
    motion["authored_batches"] = [
        next(
            (
                revised
                for revised in selected
                if revised["variant_id"] == row["variant_id"]
                and revised["segment_id"] == row["segment_id"]
            ),
            row,
        )
        for row in motion["authored_batches"]
    ]
    motion["localized_revisions"] = [
        {
            "kind": "RENDERED_LOCALIZED",
            "segment_id": "S3_THE_FORECAST_ON_RECORD",
            "critic_report_sha256": logical_hash(critic),
            "receipt": receipt_row,
            "sandbox": sandbox,
            "provenance": provenance,
        }
    ]
    motion["typecheck"] = {
        "status": "PASS",
        "stdout": typecheck.stdout[-2000:],
    }
    _write_json(motion_path, motion)
    report = {
        "schema_version": "contentops.retention_native.localized_revision.v1",
        "status": "PASS_LOCALIZED_S3_CX_XHIGH_REVISION",
        "segment_id": "S3_THE_FORECAST_ON_RECORD",
        "issues_addressed": material,
        "receipt": receipt_row,
        "sandbox": sandbox,
        "provenance": provenance,
        "typecheck": motion["typecheck"],
        "public_write": False,
    }
    _write_json(runtime / "localized_revision_report_v1.json", report)
    return report


def _mechanical_index(rows: Sequence[Mapping[str, Any]]) -> str:
    imports = [
        "import React from 'react';",
        "import {AbsoluteFill, Sequence} from 'remotion';",
        "import type {VariantProps} from '../types';",
    ]
    for row in rows:
        module = "./" + Path(str(row["required_path"])).stem
        imports.append(f"import {{{row['component_name']}}} from '{module}';")
    body: list[str] = [*imports, ""]
    totals: dict[str, int] = {}
    for variant, export_name in (
        ("short_9x16", "ShortVideo"),
        ("midform_16x9", "MidformVideo"),
    ):
        selected = [row for row in rows if row["variant_id"] == variant]
        offset = 0
        body.append(
            f"export const {export_name}: React.FC<VariantProps> = (props) => ("
        )
        body.append("  <AbsoluteFill style={{backgroundColor: '#081018'}}>")
        for row in selected:
            duration = int(row["duration_frames"])
            body.append(
                f'    <Sequence from={{{offset}}} durationInFrames={{{duration}}} name="{row["segment_id"]}">'
            )
            body.append(f"      <{row['component_name']} {{...props}} />")
            body.append("    </Sequence>")
            offset += duration
        body.extend(("  </AbsoluteFill>", ");", ""))
        totals[variant] = offset
    body.append(f"export const shortDurationFrames = {totals['short_9x16']};")
    body.append(f"export const midformDurationFrames = {totals['midform_16x9']};")
    body.append(
        "export const authoredSegments: Array<{id: string; component: React.FC<VariantProps>; durationInFrames: number; width: number; height: number}> = ["
    )
    for row in rows:
        width = 1080 if row["variant_id"] == "short_9x16" else 1920
        height = 1920 if row["variant_id"] == "short_9x16" else 1080
        body.append(
            f"  {{id: '{row['composition_id']}', component: {row['component_name']}, "
            f"durationInFrames: {int(row['duration_frames'])}, width: {width}, height: {height}}},"
        )
    body.append("];")
    return "\n".join(body) + "\n"


def render_motion(
    *, runtime: Path, repo_root: Path, node: str = "node"
) -> dict[str, Any]:
    motion = _read_json(runtime / "motion_authorship_manifest_v2.json")
    if motion.get("provenance_broken") or motion.get("degraded_creative_model"):
        raise RuntimeError("motion_manifest_not_renderable")
    renderer = (repo_root / RENDERER_RELATIVE).resolve()
    public_dir = runtime / "render_public"
    render_script = renderer / "scripts" / "render.mjs"
    results: dict[str, Any] = {}
    segment_cache: dict[str, Any] = {}
    authorship_sha256 = logical_hash(motion["authored_batches"])
    # Render one proxy per authored segment first. These are the selective-rerender cache
    # units and the direct input to temporal motion strips/localized revision evidence.
    for row in motion["authored_batches"]:
        key = logical_hash(
            {
                "composition_id": row["composition_id"],
                "model_output_sha256": row["model_output_sha256"],
                "duration_frames": row["duration_frames"],
                "captions_visible": False,
                "scale": 0.5,
            }
        )
        output = (
            runtime
            / "render_cache"
            / "segments"
            / row["variant_id"]
            / f"{row['segment_id']}-{key[:18]}.mp4"
        )
        receipt = output.with_suffix(".receipt.json")
        props = output.with_suffix(".props.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        _write_json(props, {"captionsVisible": False, "assetBase": "assets"})
        cache_hit = output.is_file() and receipt.is_file()
        if not cache_hit:
            _run(
                [
                    node,
                    str(render_script),
                    "--composition",
                    row["composition_id"],
                    "--output",
                    str(output),
                    "--public-dir",
                    str(public_dir),
                    "--props",
                    str(props),
                    "--receipt",
                    str(receipt),
                    "--scale",
                    "0.5",
                ],
                cwd=renderer,
                timeout=3600,
            )
        segment_cache[f"{row['variant_id']}:{row['segment_id']}"] = {
            "cache_key": key,
            "cache_hit": cache_hit,
            "path": str(output),
            "sha256": sha256_file(output),
            "receipt_path": str(receipt),
            "beat_ids": row["beat_ids"],
        }
    for variant, composition in (
        ("short_9x16", "ConcreteFirstShort"),
        ("midform_16x9", "ConcreteFirstMidform"),
    ):
        variant_rows: dict[str, Any] = {}
        for mode, captions, scale in (
            ("proxy", True, 0.5),
            ("proxy_captions_hidden", False, 0.5),
            ("full", True, 1.0),
            ("full_captions_hidden", False, 1.0),
        ):
            props = runtime / "contracts" / "render" / f"{variant}_{mode}_props.json"
            receipt = runtime / "receipts" / "render" / f"{variant}_{mode}.json"
            output = runtime / "render_cache" / "silent" / f"{variant}_{mode}.mp4"
            _write_json(
                props,
                {
                    "captionsVisible": captions,
                    "assetBase": "assets",
                    "authorshipSha256": authorship_sha256,
                },
            )
            cached_receipt = _read_json(receipt) if receipt.is_file() else {}
            cache_hit = (
                output.is_file()
                and receipt.is_file()
                and cached_receipt.get("authorship_sha256") == authorship_sha256
            )
            if not cache_hit:
                _run(
                    [
                        node,
                        str(render_script),
                        "--composition",
                        composition,
                        "--output",
                        str(output),
                        "--public-dir",
                        str(public_dir),
                        "--props",
                        str(props),
                        "--receipt",
                        str(receipt),
                        "--scale",
                        str(scale),
                    ],
                    cwd=renderer,
                    timeout=5400,
                )
            variant_rows[mode] = {
                "path": str(output),
                "sha256": sha256_file(output),
                "receipt": _read_json(receipt),
                "cache_hit": cache_hit,
            }
        results[variant] = variant_rows
    manifest = {
        "schema_version": "contentops.retention_native.motion_render.v2",
        "video_id": VIDEO_ID,
        "variants": results,
        "segment_proxy_cache": segment_cache,
        "selective_rerender_unit": "variant_segment_component",
        "authorship_sha256": authorship_sha256,
        "network_calls": 0,
        "uploads": 0,
        "public_write": False,
    }
    _write_json(runtime / "motion_render_manifest_v2.json", manifest)
    return manifest


def _parse_loudnorm(stderr: str) -> dict[str, Any]:
    matches = list(re.finditer(r"\{\s*\"input_i\".*?\}", stderr, flags=re.DOTALL))
    if not matches:
        raise RuntimeError("ffmpeg_loudnorm_json_missing")
    return json.loads(matches[-1].group(0))


def _measure_loudness(path: Path, ffmpeg: str) -> dict[str, float]:
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
            "-f",
            "null",
            "NUL",
        ],
        capture_output=True,
        text=True,
        timeout=1200,
        check=False,
    )
    value = _parse_loudnorm(result.stderr)
    return {
        "integrated_lufs": float(value["input_i"]),
        "true_peak_dbtp": float(value["input_tp"]),
    }


def build_audio_and_mux(
    *, runtime: Path, tts_python: str, ffmpeg: str, ffprobe: str
) -> dict[str, Any]:
    video_id = _runtime_video_id(runtime)
    segments = _read_json(runtime / "contracts" / "segment_authorship_v2.json")
    renders = _read_json(runtime / "motion_render_manifest_v2.json")
    results: dict[str, Any] = {}
    for variant in ("short_9x16", "midform_16x9"):
        beats = segments[f"{variant}_beats"]
        duration = float(segments["durations_seconds"][variant])
        narration_text = " ".join(str(beat["narration"]) for beat in beats)
        narration = runtime / "audio" / variant / "narration.wav"
        narration.parent.mkdir(parents=True, exist_ok=True)
        request = runtime / "contracts" / "audio" / f"{variant}_kokoro_request.json"
        _write_json(
            request,
            {
                "schema_version": "contentops.retention_native.kokoro_batch_request.v2",
                "segments": [
                    {
                        "beat_id": f"{variant}-narration",
                        "text": narration_text.replace("EIA", "E I A"),
                        "voice": "af_heart",
                        "speed": 1.13 if variant == "short_9x16" else 1.0,
                        "output_path": str(narration),
                    }
                ],
            },
        )
        worker = _run(
            [
                tts_python,
                "-m",
                "live_contentops.video_tts_worker_v1",
                "--batch-request",
                str(request),
            ],
            cwd=Path.cwd(),
            timeout=5400,
        )
        state_timeline: list[dict[str, Any]] = []
        sfx: list[dict[str, Any]] = []
        at = 0.0
        for beat in beats:
            beat_duration = float(beat["duration_seconds"])
            state_timeline.append(
                {
                    "start_seconds": at,
                    "end_seconds": at + beat_duration,
                    "state": beat["audio_state"],
                }
            )
            if beat["sfx_kind"] != "none":
                sfx.append(
                    {
                        "cue_id": f"{variant}-{beat['beat_id']}",
                        "kind": beat["sfx_kind"],
                        "at_seconds": at
                        + beat_duration * float(beat["sfx_at_fraction"]),
                        "authored_intent": beat.get("sfx_intent"),
                    }
                )
            at += beat_duration
        score = render_owned_score(
            duration_seconds=duration,
            state_timeline=state_timeline,
            sfx_cues=sfx,
            output_dir=runtime / "audio" / variant / "score",
        )
        premaster = runtime / "audio" / variant / "premaster.wav"
        master = runtime / "audio" / variant / "master.wav"
        _run(
            [
                ffmpeg,
                "-y",
                "-v",
                "error",
                "-i",
                str(narration),
                "-i",
                str(score["music"]["path"]),
                "-i",
                str(score["sfx"]["path"]),
                "-filter_complex",
                f"[0:a]apad,atrim=0:{duration},volume=1.0[n];[1:a]atrim=0:{duration},volume=0.17[m];[2:a]atrim=0:{duration},volume=0.62[s];[n][m][s]amix=inputs=3:duration=longest:normalize=0,atrim=0:{duration}[a]",
                "-map",
                "[a]",
                "-ar",
                "48000",
                "-ac",
                "2",
                str(premaster),
            ],
            timeout=1800,
        )
        _run(
            [
                ffmpeg,
                "-y",
                "-v",
                "error",
                "-i",
                str(premaster),
                "-af",
                "loudnorm=I=-16:TP=-1.8:LRA=11",
                "-ar",
                "48000",
                "-ac",
                "2",
                str(master),
            ],
            timeout=1800,
        )
        measurement = _measure_loudness(master, ffmpeg)
        if not -17 <= measurement["integrated_lufs"] <= -15:
            raise RuntimeError(
                f"audio_loudness_outside_contract:{variant}:{measurement}"
            )
        if measurement["true_peak_dbtp"] > -1.5:
            raise RuntimeError(
                f"audio_true_peak_outside_contract:{variant}:{measurement}"
            )
        output_rows: dict[str, Any] = {}
        for mode, silent_key, suffix in (
            ("final", "full", ""),
            ("captions_hidden", "full_captions_hidden", "_captions_hidden"),
        ):
            output = runtime / "outputs" / f"{variant}{suffix}.mp4"
            output.parent.mkdir(parents=True, exist_ok=True)
            _run(
                [
                    ffmpeg,
                    "-y",
                    "-v",
                    "error",
                    "-i",
                    renders["variants"][variant][silent_key]["path"],
                    "-i",
                    str(master),
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-shortest",
                    str(output),
                ],
                timeout=1800,
            )
            output_rows[mode] = {"path": str(output), "sha256": sha256_file(output)}
        results[variant] = {
            "duration_seconds": duration,
            "narration": {
                "path": str(narration),
                "sha256": sha256_file(narration),
                "provider": "kokoro",
                "model": "Kokoro-82M",
                "voice": "af_heart",
                "network_calls": 0,
            },
            "worker_stdout_tail": worker.stdout[-1000:],
            "score": score,
            "master": {
                "path": str(master),
                "sha256": sha256_file(master),
                "measurement": measurement,
            },
            "outputs": output_rows,
        }
    manifest = {
        "schema_version": "contentops.retention_native.audio_mux.v2",
        "video_id": video_id,
        "variants": results,
        "target_integrated_lufs": -16.0,
        "true_peak_dbtp_max": -1.5,
        "network_calls": 0,
        "uploads": 0,
        "public_write": False,
    }
    _write_json(runtime / "audio_mux_manifest_v2.json", manifest)
    return manifest


def probe_media(*, runtime: Path, ffprobe: str) -> dict[str, Any]:
    video_id = _runtime_video_id(runtime)
    audio = _read_json(runtime / "audio_mux_manifest_v2.json")
    expected = {
        "short_9x16": (1080, 1920, 45.0, 60.0),
        "midform_16x9": (1920, 1080, 90.0, 150.0),
    }
    rows: dict[str, Any] = {}
    for variant, (width, height, minimum, maximum) in expected.items():
        variants: dict[str, Any] = {}
        for mode in ("final", "captions_hidden"):
            path = Path(audio["variants"][variant]["outputs"][mode]["path"])
            raw = _run(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-show_streams",
                    "-show_format",
                    "-of",
                    "json",
                    str(path),
                ],
                timeout=300,
            )
            probe = json.loads(raw.stdout)
            video = next(
                row for row in probe["streams"] if row["codec_type"] == "video"
            )
            sound = next(
                row for row in probe["streams"] if row["codec_type"] == "audio"
            )
            duration = float(probe["format"]["duration"])
            blockers: list[str] = []
            if (int(video["width"]), int(video["height"])) != (width, height):
                blockers.append("dimensions")
            if video["codec_name"] != "h264" or sound["codec_name"] != "aac":
                blockers.append("codecs")
            if not minimum <= duration <= maximum + 0.5:
                blockers.append("duration")
            variants[mode] = {
                "path": str(path),
                "sha256": sha256_file(path),
                "duration_seconds": duration,
                "width": int(video["width"]),
                "height": int(video["height"]),
                "video_codec": video["codec_name"],
                "audio_codec": sound["codec_name"],
                "fps": video.get("avg_frame_rate"),
                "size_bytes": path.stat().st_size,
                "status": "PASS" if not blockers else "BLOCK",
                "blockers": blockers,
            }
            if blockers:
                raise RuntimeError(
                    f"final_media_probe_block:{variant}:{mode}:{blockers}"
                )
        rows[variant] = variants
    report = {
        "schema_version": "contentops.retention_native.final_media_probe.v2",
        "video_id": video_id,
        "variants": rows,
        "status": "PASS",
        "public_write": False,
    }
    _write_json(runtime / "final_media_probe_v2.json", report)
    return report


def remux_existing_audio(*, runtime: Path, ffmpeg: str) -> dict[str, Any]:
    """Bind previously accepted masters to revised silent renders without re-authoring."""
    renders = _read_json(runtime / "motion_render_manifest_v2.json")
    audio_path = runtime / "audio_mux_manifest_v2.json"
    audio = _read_json(audio_path)
    for variant in ("short_9x16", "midform_16x9"):
        master = Path(audio["variants"][variant]["master"]["path"])
        if not master.is_file():
            raise RuntimeError(f"accepted_audio_master_missing:{variant}")
        output_rows: dict[str, Any] = {}
        for mode, silent_key, suffix in (
            ("final", "full", ""),
            ("captions_hidden", "full_captions_hidden", "_captions_hidden"),
        ):
            output = runtime / "outputs" / f"{variant}{suffix}.mp4"
            _run(
                [
                    ffmpeg,
                    "-y",
                    "-v",
                    "error",
                    "-i",
                    str(renders["variants"][variant][silent_key]["path"]),
                    "-i",
                    str(master),
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-shortest",
                    str(output),
                ],
                timeout=1800,
            )
            output_rows[mode] = {
                "path": str(output),
                "sha256": sha256_file(output),
            }
        audio["variants"][variant]["outputs"] = output_rows
        audio["variants"][variant]["remuxed_to_authorship_sha256"] = renders[
            "authorship_sha256"
        ]
    audio["remux_mode"] = "REUSE_ACCEPTED_AUDIO_MASTERS_AFTER_LOCALIZED_VISUAL_REVISION"
    _write_json(audio_path, audio)
    return audio


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage", choices=("author", "render", "audio", "remux", "probe")
    )
    parser.add_argument("--runtime", default=str(DEFAULT_RUNTIME))
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--node", default="node")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument(
        "--tts-python",
        default=r"A:\Capital Chronicle\Runtime\ContentOps\tier2\tts-kokoro-venv\Scripts\python.exe",
    )
    args = parser.parse_args()
    runtime = Path(args.runtime).resolve()
    repo_root = Path(args.repo_root).resolve()
    if args.stage == "author":
        result = author_motion(runtime=runtime, repo_root=repo_root)
    elif args.stage == "render":
        result = render_motion(runtime=runtime, repo_root=repo_root, node=args.node)
    elif args.stage == "audio":
        result = build_audio_and_mux(
            runtime=runtime,
            tts_python=args.tts_python,
            ffmpeg=args.ffmpeg,
            ffprobe=args.ffprobe,
        )
    elif args.stage == "remux":
        result = remux_existing_audio(runtime=runtime, ffmpeg=args.ffmpeg)
    else:
        result = probe_media(runtime=runtime, ffprobe=args.ffprobe)
    print(
        json.dumps(
            {
                "status": "PASS",
                "stage": args.stage,
                "result_sha256": logical_hash(result),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
