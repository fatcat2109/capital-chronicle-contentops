"""Independent, bounded multimodal critic for local retention-native V2 proofs.

The critic consumes frame and motion-strip samples derived from the exact finished
media, not story evidence, and has presentation-only authority.  It routes through
the canonical ordered 9Router seam, records exact model identity and hashes, and
cannot grant publication or factual authority.  Audio is explicitly out of scope
when the selected model boundary cannot audition it.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import mimetypes
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from .content_intelligence_contracts_v2 import logical_hash
from .media_manifest_authority_v1 import sha256_file
from .nine_router_llm_seam_v2 import ROLE_MULTIMODAL_VIDEO_CRITIC, routed_llm_invocation
from .nine_router_ordered_model_router_v2 import ACCEPTED
from .nine_router_provider_adapter_v2 import call_nine_router


SCHEMA_VERSION = "contentops.retention_native.independent_multimodal_critic.v2"
PROMPT_TEMPLATE = "retention_native_independent_multimodal_critic"
PROMPT_VERSION = "v2"
CANONICAL_CRITIC_PROMPT = """You are the independent senior video editor and visual critic for a financial-news proof. You did not author this work. Apply a demanding, specific standard; do not reward mere technical validity.

Review the labeled rendered images in sequence. Contact sheets sample the full edit; stills show exact full-resolution frames; motion strips show ordered frames from the actual hook/payoff clips and captions-hidden motion clips. Use the strips to assess evolution and edit rhythm rather than treating them as unrelated thumbnails. Judge hook clarity, payoff visibility, primary-visual evolution with captions hidden, native 9:16 and 16:9 composition, chart/document legibility, visual repetition, hierarchy, polish, rights/source labels, and forecast-versus-observation boundaries. Technical audio facts are supplied, but you cannot hear audio in these images: do not claim to have judged narrator naturalness, pronunciation, music taste, or SFX taste. Record that limitation.

Return ONLY one JSON object. Required shape:
{
  "status":"PASS|PASS_WITH_NOTES|REVISE|BLOCK",
  "summary":"concise high-bar verdict",
  "scope":{"visual_images_reviewed":true,"actual_finished_media_sampled":true,"audio_listened":false,"audio_technical_metrics_reviewed":true,"limitations":["..."]},
  "issues":[{
    "severity":"BLOCKER|MAJOR|MINOR|NOTE",
    "video_id":"exact video id from technical context",
    "variant_id":"short_9x16|midform_16x9",
    "scene_id":"one exact scene id for this issue",
    "start_seconds":number,
    "end_seconds":number,
    "beat_ids":["exact beat ids"],
    "category":"hook|payoff|visual|edit|caption|audio|rights|evidence",
    "observation":"specific visible or technical issue",
    "structural_fix":"exact beat/edit/asset/audio-level correction"
  }],
  "strengths":["specific strengths"],
  "acceptance_recommendation":"one sentence"
}

Every issue must identify exactly one scene_id. Split an observation into separate issues when it affects multiple scenes. video_id and scene_id must be nonempty exact IDs, beat_ids must contain the exact nonempty beat IDs for that one scene, and start_seconds/end_seconds must be numeric with 0 <= start_seconds <= end_seconds. If any BLOCKER or MAJOR issue exists, status must be REVISE or BLOCK. If no material issue exists, use PASS or PASS_WITH_NOTES. Pay particular attention to whether landscape charts are meaningfully legible in the vertical cut and whether dark typographic frames become a repetitive template. Never invent a factual error from an unreadable thumbnail; report legibility as a presentation issue."""


def canonical_critic_repair_prompt(original: str, diagnostic: str | None) -> str:
    return (
        original
        + "\n\nSTRUCTURED REPAIR REQUIRED. The prior response failed: "
        + str(diagnostic or "schema_invalid")
        + ". Return the entire JSON again. Every issue, including global/style issues, must name the exact nonempty video_id, exactly one exact nonempty scene_id, numeric start_seconds/end_seconds with 0 <= start_seconds <= end_seconds, and one or more exact nonempty beat IDs from technical_context.beat_timeline. Split multi-scene observations into one issue per scene; never omit localization and never use a wildcard."
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path.name}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _critic_proxy(source: Path, *, label: str, root: Path) -> Path:
    from PIL import Image  # type: ignore

    safe = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    target = root / "review" / "critic_inputs" / f"{safe}.jpg"
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as opened:
        image = opened.convert("RGB")
        image.thumbnail((1600, 1600))
        image.save(target, format="JPEG", quality=84, optimize=True, progressive=True)
    return target


def _extract_json(text: str) -> Mapping[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[1] if "\n" in candidate else candidate
        if candidate.endswith("```"):
            candidate = candidate[:-3]
    candidate = candidate.strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as original_error:
        decoder = json.JSONDecoder()
        value = None
        for match in re.finditer(r"\{", candidate):
            try:
                decoded, _end = decoder.raw_decode(candidate[match.start():])
            except json.JSONDecodeError:
                continue
            if isinstance(decoded, Mapping):
                value = decoded
                break
        if value is None:
            raise original_error
    if not isinstance(value, Mapping):
        raise ValueError("critic_json_object_required")
    return value


def _is_exact_nonempty_id(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and not any(character.isspace() for character in value)
        and not any(character in "*?[]" for character in value)
    )


def validate_critic_output(text: str) -> tuple[bool, str | None, Any, str | None]:
    try:
        value = dict(_extract_json(text))
    except Exception:
        return False, "structured_output_malformed", None, "critic_json_parse_failed"
    issues = value.get("issues")
    if value.get("status") not in {"PASS", "PASS_WITH_NOTES", "REVISE", "BLOCK"}:
        return False, "structured_output_schema_invalid", None, "critic_status_invalid"
    authored_keys = {
        "status",
        "summary",
        "scope",
        "issues",
        "strengths",
        "acceptance_recommendation",
    }
    if not authored_keys <= set(value):
        return False, "structured_output_schema_invalid", None, "critic_authored_shape_incomplete"
    if not isinstance(value.get("summary"), str) or not value["summary"].strip():
        return False, "structured_output_schema_invalid", None, "critic_summary_required"
    scope = value.get("scope")
    if (
        not isinstance(scope, Mapping)
        or scope.get("visual_images_reviewed") is not True
        or scope.get("actual_finished_media_sampled") is not True
        or scope.get("audio_listened") is not False
        or scope.get("audio_technical_metrics_reviewed") is not True
        or not isinstance(scope.get("limitations"), list)
        or not scope["limitations"]
        or any(not isinstance(row, str) or not row.strip() for row in scope["limitations"])
    ):
        return False, "structured_output_schema_invalid", None, "critic_scope_invalid"
    strengths = value.get("strengths")
    if (
        not isinstance(strengths, list)
        or not strengths
        or any(not isinstance(row, str) or not row.strip() for row in strengths)
    ):
        return False, "structured_output_schema_invalid", None, "critic_strengths_required"
    if (
        not isinstance(value.get("acceptance_recommendation"), str)
        or not value["acceptance_recommendation"].strip()
    ):
        return False, "structured_output_schema_invalid", None, "critic_acceptance_recommendation_required"
    if not isinstance(issues, list):
        return False, "structured_output_schema_invalid", None, "critic_issues_list_required"
    required = {
        "severity",
        "video_id",
        "variant_id",
        "scene_id",
        "start_seconds",
        "end_seconds",
        "beat_ids",
        "category",
        "observation",
        "structural_fix",
    }
    for index, issue in enumerate(issues):
        if not isinstance(issue, Mapping) or not required <= set(issue):
            return False, "structured_output_schema_invalid", None, f"critic_issue_shape_invalid:{index}"
        if issue.get("severity") not in {"BLOCKER", "MAJOR", "MINOR", "NOTE"}:
            return False, "structured_output_schema_invalid", None, f"critic_issue_severity_invalid:{index}"
        if not _is_exact_nonempty_id(issue.get("video_id")):
            return False, "structured_output_schema_invalid", None, f"critic_issue_video_id_required:{index}"
        if issue.get("variant_id") not in {"short_9x16", "midform_16x9"}:
            return False, "structured_output_schema_invalid", None, f"critic_issue_variant_invalid:{index}"
        if not _is_exact_nonempty_id(issue.get("scene_id")):
            return False, "structured_output_schema_invalid", None, f"critic_issue_scene_id_required:{index}"
        start_seconds = issue.get("start_seconds")
        end_seconds = issue.get("end_seconds")
        if (
            isinstance(start_seconds, bool)
            or not isinstance(start_seconds, (int, float))
            or not math.isfinite(start_seconds)
            or start_seconds < 0
        ):
            return False, "structured_output_schema_invalid", None, f"critic_issue_start_seconds_invalid:{index}"
        if (
            isinstance(end_seconds, bool)
            or not isinstance(end_seconds, (int, float))
            or not math.isfinite(end_seconds)
            or end_seconds < start_seconds
        ):
            return False, "structured_output_schema_invalid", None, f"critic_issue_end_seconds_invalid:{index}"
        beat_ids = issue.get("beat_ids")
        if (
            not isinstance(beat_ids, list)
            or not beat_ids
            or any(not _is_exact_nonempty_id(beat_id) for beat_id in beat_ids)
            or len(set(beat_ids)) != len(beat_ids)
        ):
            return False, "structured_output_schema_invalid", None, f"critic_issue_beat_ids_required:{index}"
        if issue.get("category") not in {"hook", "payoff", "visual", "edit", "caption", "audio", "rights", "evidence"}:
            return False, "structured_output_schema_invalid", None, f"critic_issue_category_invalid:{index}"
        if not isinstance(issue.get("observation"), str) or not issue["observation"].strip():
            return False, "structured_output_schema_invalid", None, f"critic_issue_observation_required:{index}"
        if not isinstance(issue.get("structural_fix"), str) or not issue["structural_fix"].strip():
            return False, "structured_output_schema_invalid", None, f"critic_issue_structural_fix_required:{index}"
    material = any(row.get("severity") in {"BLOCKER", "MAJOR"} for row in issues)
    if material and value["status"] not in {"REVISE", "BLOCK"}:
        return False, "structured_output_schema_invalid", None, "critic_material_issue_requires_revise"
    if not material and value["status"] in {"REVISE", "BLOCK"}:
        return False, "structured_output_schema_invalid", None, "critic_revise_requires_material_issue"
    return True, None, value, None


def run_independent_critic(*, package_root: str | Path, output_path: str | Path) -> dict[str, Any]:
    root = Path(package_root).resolve()
    request = _read_json(root / "independent_critic_request_v2.json")
    diagnostics = _read_json(root / "retention_diagnostics_v2.json")
    review = _read_json(root / "review_media_manifest_v2.json")
    render_manifest = _read_json(root / "variant_render_manifest_v2.json")
    opportunity = _read_json(root / "contracts" / "video_opportunity_v2.json")
    source_images: list[tuple[str, Path]] = []
    for variant_id in ("short_9x16", "midform_16x9"):
        variant = review["variants"][variant_id]
        source_images.append((f"{variant_id} contact sheet", Path(variant["contact_sheet"])))
        source_images.append((f"{variant_id} hook and payoff motion strip", Path(variant["review_motion_strip"])))
        for row in variant["stills"]:
            if row["name"] in {"hook", "payoff"}:
                source_images.append((f"{variant_id} {row['name']} still at {row['at_seconds']}s", Path(row["path"])))
        source_images.append((
            f"{variant_id} captions-hidden motion strip",
            Path(review["caption_hidden"][variant_id]["motion_strip_path"]),
        ))
    for label, path in source_images:
        if not path.is_file():
            raise RuntimeError(f"critic_image_missing:{label}")
    images = [(label, _critic_proxy(path, label=label, root=root)) for label, path in source_images]

    instruction = CANONICAL_CRITIC_PROMPT
    technical = {
        "video_id": opportunity["video_id"],
        "request_scope": request["review_scope"],
        "diagnostics": diagnostics,
        "beat_timeline": {
            variant_id: render_manifest["assemblies"][variant_id]["beat_timeline"]
            for variant_id in ("short_9x16", "midform_16x9")
        },
        "image_labels_and_hashes": [{"label": label, "sha256": sha256_file(path)} for label, path in images],
        "chatgpt_jim_acceptance": "PENDING",
        "public_write_authority": False,
    }
    input_artifacts = []
    for variant_id in ("short_9x16", "midform_16x9"):
        output = request["outputs"][variant_id]
        variant_review = review["variants"][variant_id]
        hidden = review["caption_hidden"][variant_id]
        input_artifacts.extend([
            {"kind": "finished_output", "variant_id": variant_id, "path": output["path"], "sha256": output["sha256"]},
            {"kind": "representative_review_clip", "variant_id": variant_id, "path": variant_review["review_clip"], "sha256": variant_review["review_clip_sha256"]},
            {"kind": "captions_hidden_motion_clip", "variant_id": variant_id, "path": hidden["path"], "sha256": hidden["sha256"]},
            {"kind": "captions_hidden_motion_strip", "variant_id": variant_id, "path": hidden["motion_strip_path"], "sha256": hidden["motion_strip_sha256"]},
        ])
    image_content: list[dict[str, Any]] = []
    for label, path in images:
        image_content.append({"type": "text", "text": f"IMAGE LABEL: {label}"})
        image_content.append({"type": "image_url", "image_url": {"url": _data_uri(path), "detail": "high"}})

    def provider_call(current_prompt: str, model: str, timeout: float):
        content = [
            {"type": "text", "text": current_prompt + "\n\nTechnical context:\n" + json.dumps(technical, sort_keys=True)},
            *image_content,
        ]
        return call_nine_router(content, model, timeout, max_tokens=6000, temperature=0.1)

    def repair_prompt_builder(original: str, _bad_output: str, diagnostic: str | None) -> str:
        return canonical_critic_repair_prompt(original, diagnostic)

    invocation = routed_llm_invocation(
        prompt=instruction,
        role_task_id=ROLE_MULTIMODAL_VIDEO_CRITIC,
        logical_invocation_id=f"inv_video_critic_{logical_hash(technical)[:20]}",
        work_item_id=str(request.get("outputs", {}).get("short_9x16", {}).get("sha256") or "retention-native-v2")[:32],
        timeout_seconds=300.0,
        validator=validate_critic_output,
        provider_call=provider_call,
        governed_input=technical,
        prompt_template=PROMPT_TEMPLATE,
        prompt_version=PROMPT_VERSION,
        repair_prompt_builder=repair_prompt_builder,
    )
    if invocation.get("terminal_disposition") != ACCEPTED:
        _write_json(Path(output_path).resolve(), {
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCK",
            "independent_of_director": True,
            "error": "critic_router_did_not_accept_output",
            "router_evidence": {key: invocation.get(key) for key in (
                "authority_id", "terminal_disposition", "selected_model", "models_attempted_in_order",
                "total_attempts", "total_fallback_transitions", "total_structured_repair_attempts",
                "total_usage", "total_cost", "budget_exhausted_reason", "model_identity_note", "attempts",
            )},
            "input_images": [{"label": label, "path": str(path), "sha256": sha256_file(path)} for label, path in images],
            "input_artifacts": input_artifacts,
            "raw_image_bytes_persisted_in_report": False,
            "public_write": False,
        })
        raise RuntimeError(f"critic_router_blocked:{invocation.get('terminal_disposition')}")
    accepted_output = invocation["output"]
    authored_keys = (
        "status",
        "summary",
        "scope",
        "issues",
        "strengths",
        "acceptance_recommendation",
    )
    if (
        not isinstance(accepted_output, Mapping)
        or set(accepted_output) != set(authored_keys)
        or not isinstance(accepted_output.get("summary"), str)
        or not isinstance(accepted_output.get("scope"), Mapping)
        or not isinstance(accepted_output.get("strengths"), list)
        or not all(isinstance(row, str) and row.strip() for row in accepted_output["strengths"])
        or not isinstance(accepted_output.get("acceptance_recommendation"), str)
    ):
        raise RuntimeError("critic_router_accepted_output_shape_incomplete")
    report = {key: accepted_output[key] for key in authored_keys}
    scope = dict(report.get("scope") or {})
    scope.update({
        "visual_images_reviewed": True,
        "actual_finished_media_sampled": True,
        "finished_media_sampling_method": "contact_sheets_stills_and_ordered_motion_strips_derived_from_bound_mp4s",
        "audio_listened": False,
        "audio_technical_metrics_reviewed": True,
    })
    limitations = list(scope.get("limitations") or ())
    if not limitations:
        limitations.append("Audio was not auditioned; only supplied codec, loudness, peak, and coverage diagnostics were reviewed.")
    scope["limitations"] = limitations
    report["scope"] = scope
    report.update({
        "schema_version": SCHEMA_VERSION,
        "independent_of_director": True,
        "critic_identity": {
            "kind": "canonical_9router_multimodal_model",
            "selected_model": invocation.get("selected_model"),
            "gateway": invocation.get("gateway"),
            "model_identity_note": invocation.get("model_identity_note"),
        },
        "router_evidence": {key: invocation.get(key) for key in (
            "authority_id", "terminal_disposition", "selected_model", "models_attempted_in_order",
            "total_attempts", "total_fallback_transitions", "total_structured_repair_attempts",
            "total_usage", "total_cost", "model_identity_note",
        )},
        "input_images": [{"label": label, "path": str(path), "sha256": sha256_file(path)} for label, path in images],
        "input_artifacts": input_artifacts,
        "raw_image_bytes_persisted_in_report": False,
        "publication_authority": False,
        "factual_authority": False,
        "public_write": False,
    })
    accepted_attempts = list(invocation.get("attempts") or ())
    if (
        not accepted_attempts
        or accepted_attempts[-1].get("disposition") != "accepted"
        or not accepted_attempts[-1].get("output_hash")
        or not invocation.get("accepted_validated_output_sha256")
        or accepted_attempts[-1].get("validated_output_sha256")
        != invocation.get("accepted_validated_output_sha256")
    ):
        raise RuntimeError("critic_router_accepted_attempt_evidence_missing")
    receipt_path = (root / "receipts" / "canonical_critic_router_execution_v2.json").resolve()
    receipt = {
        "schema_version": "contentops.retention_native.canonical_critic_router_execution.v2",
        "status": "PASS",
        "authority_id": invocation.get("authority_id"),
        "gateway": invocation.get("gateway"),
        "logical_invocation_id": invocation.get("logical_invocation_id"),
        "work_item_id": invocation.get("work_item_id"),
        "role_task_id": invocation.get("role_task_id"),
        "terminal_disposition": invocation.get("terminal_disposition"),
        "selected_model": invocation.get("selected_model"),
        "models_attempted_in_order": invocation.get("models_attempted_in_order"),
        "total_attempts": invocation.get("total_attempts"),
        "total_fallback_transitions": invocation.get("total_fallback_transitions"),
        "total_structured_repair_attempts": invocation.get("total_structured_repair_attempts"),
        "total_usage": invocation.get("total_usage"),
        "total_cost": invocation.get("total_cost"),
        "model_identity_note": invocation.get("model_identity_note"),
        "attempts": accepted_attempts,
        "prompt_logical_hashes": [row.get("prompt_logical_hash") for row in accepted_attempts],
        "governed_input": technical,
        "governed_input_hash": logical_hash(technical),
        "accepted_model_output": invocation["output"],
        "accepted_model_output_logical_sha256": logical_hash(invocation["output"]),
        "accepted_validated_output_sha256": invocation.get("accepted_validated_output_sha256"),
        "accepted_provider_output_hash": accepted_attempts[-1]["output_hash"],
        "final_critic_payload_logical_sha256": logical_hash(report),
        "review_input_binding_sha256": logical_hash({
            "input_artifacts": report["input_artifacts"],
            "input_images": report["input_images"],
        }),
        "publication_authority": False,
        "factual_authority": False,
        "public_write": False,
    }
    _write_json(receipt_path, receipt)
    report["execution_receipt"] = {
        "kind": "canonical_router",
        "path": str(receipt_path),
        "sha256": sha256_file(receipt_path),
    }
    _write_json(Path(output_path).resolve(), report)
    return report


def critic_command(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the bounded independent multimodal V2 video critic.")
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = run_independent_critic(package_root=args.package_root, output_path=args.output)
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc), "public_write": False}, sort_keys=True))
        return 1
    print(json.dumps({"status": report["status"], "issue_count": len(report["issues"]), "critic_identity": report["critic_identity"], "public_write": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(critic_command())
