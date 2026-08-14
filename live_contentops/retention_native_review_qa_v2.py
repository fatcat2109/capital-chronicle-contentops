"""Rendered review artifacts and deterministic temporal/grounding QA for V2-01."""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.media_manifest_authority_v1 import sha256_file
from live_contentops.nine_router_llm_seam_v2 import ROLE_MULTIMODAL_VIDEO_CRITIC
from live_contentops.nine_router_ordered_model_router_v2 import ACCEPTED, ProviderResult
from live_contentops.nine_router_provider_adapter_v2 import call_nine_router_v2_isolated
from live_contentops.retention_native_concrete_first_v2 import canonical_json, logical_hash
from live_contentops.retention_native_replacement_runner_v2 import DEFAULT_RUNTIME, VIDEO_ID
from live_contentops.v2_isolated_llm_execution_v1 import routed_v2_isolated_invocation
from live_contentops.retention_native_storyboard_v2 import contact_sheet

SCHEMA_VERSION = "contentops.retention_native.review_qa.v2"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8")


def _runtime_video_id(runtime: Path) -> str:
    """Use the rendered lane identity while retaining the legacy V2-01 default."""
    manifest_path = runtime / "motion_render_manifest_v2.json"
    if manifest_path.is_file():
        value = str(_read_json(manifest_path).get("video_id") or "").strip()
        if value:
            return value
    return VIDEO_ID


def _run(command: Sequence[str], *, timeout: float = 1800) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(list(command), capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"review_command_failed:{Path(command[0]).name}:{result.stderr[-1600:]}")
    return result


def _extract_frame(ffmpeg: str, video: Path, second: float, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    _run([ffmpeg, "-y", "-v", "error", "-ss", f"{second:.3f}", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(output)])


def _motion_strip(ffmpeg: str, video: Path, duration: float, output: Path) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    tile = "5x2"
    fps = max(0.05, 10.0 / max(duration, 0.1))
    _run([
        ffmpeg, "-y", "-v", "error", "-i", str(video),
        "-vf", f"fps={fps:.8f},scale=480:-1,tile={tile}:padding=6:margin=6:color=0x081018",
        "-frames:v", "1", str(output),
    ])
    return {"path": str(output), "sha256": sha256_file(output), "sample_count": 10}


def build_review_artifacts(*, runtime: Path, ffmpeg: str) -> dict[str, Any]:
    video_id = _runtime_video_id(runtime)
    renders = _read_json(runtime / "motion_render_manifest_v2.json")
    segments = _read_json(runtime / "contracts" / "segment_authorship_v2.json")
    rows: dict[str, Any] = {}
    for variant in ("short_9x16", "midform_16x9"):
        duration = float(segments["durations_seconds"][variant])
        video = Path(renders["variants"][variant]["proxy_captions_hidden"]["path"])
        frames: list[dict[str, Any]] = []
        beat_at = 0.0
        for beat in segments[f"{variant}_beats"]:
            second = beat_at + min(float(beat["duration_seconds"]) * 0.48, 2.2)
            frame = runtime / "review" / "proxy_stills" / variant / f"{beat['beat_id']}.jpg"
            _extract_frame(ffmpeg, video, second, frame)
            frames.append({"beat_id": beat["beat_id"], "path": str(frame), "sha256": sha256_file(frame)})
            beat_at += float(beat["duration_seconds"])
        sheet = contact_sheet(frames, output_path=runtime / "review" / f"{variant}_proxy_captions_hidden_contact_sheet.jpg", columns=5 if variant == "short_9x16" else 4)
        strip = _motion_strip(ffmpeg, video, duration, runtime / "review" / f"{variant}_captions_hidden_motion_strip.jpg")
        phone = None
        if variant == "short_9x16":
            phone_path = runtime / "review" / "short_9x16_phone_scale_proxy.mp4"
            _run([ffmpeg, "-y", "-v", "error", "-i", str(video), "-vf", "scale=360:640", "-an", "-c:v", "libx264", "-crf", "24", str(phone_path)])
            phone = {"path": str(phone_path), "sha256": sha256_file(phone_path), "width": 360, "height": 640}
        rows[variant] = {"stills": frames, "contact_sheet": sheet, "motion_strip": strip, "phone_scale": phone}
    manifest = {
        "schema_version": "contentops.retention_native.review_artifacts.v2",
        "video_id": video_id,
        "captions_hidden": True,
        "variants": rows,
        "derived_from_proxy_hashes": {
            variant: renders["variants"][variant]["proxy_captions_hidden"]["sha256"]
            for variant in ("short_9x16", "midform_16x9")
        },
        "public_write": False,
    }
    _write_json(runtime / "review_media_manifest_v2.json", manifest)
    return manifest


def deterministic_qa(*, runtime: Path) -> dict[str, Any]:
    video_id = _runtime_video_id(runtime)
    segments = _read_json(runtime / "contracts" / "segment_authorship_v2.json")
    storyboard = _read_json(runtime / "storyboard_animatic_manifest_v2.json")
    renders = _read_json(runtime / "motion_render_manifest_v2.json")
    variants: dict[str, Any] = {}
    for variant in ("short_9x16", "midform_16x9"):
        beats = segments[f"{variant}_beats"]
        transitions = [str(beat["transition_intent"]).lower() for beat in beats]
        easings = [str(beat["timing_easing"]).lower() for beat in beats]
        motions = [str(beat["motion_intent"]).lower() for beat in beats]
        durations = [round(float(beat["duration_seconds"]), 2) for beat in beats]
        visual_classes = [str(beat["primary_visual_type"]) for beat in beats]
        def concentration(values: Sequence[Any]) -> float:
            counts = Counter(values)
            return max(counts.values()) / len(values) if values else 1.0
        longest_static = max((duration for duration, motion in zip(durations, motions) if any(term in motion for term in ("hold", "still", "static"))), default=0.0)
        abstract_run = 0.0
        longest_abstract = 0.0
        for duration, visual in zip(durations, visual_classes):
            if visual in {"pure_abstraction", "typography_only"}:
                abstract_run += duration
                longest_abstract = max(longest_abstract, abstract_run)
            else:
                abstract_run = 0.0
        blockers: list[str] = []
        if storyboard["variants"][variant]["must_use_asset_compliance"]["status"] != "PASS":
            blockers.append("must_use_asset_compliance")
        if storyboard["variants"][variant]["visual_mix"]["status"] != "PASS":
            blockers.append("abstract_visual_mix")
        if longest_abstract > 8.0:
            blockers.append("abstract_only_run")
        if longest_static > 9.0:
            blockers.append("long_static_run")
        if concentration(transitions) > 0.72:
            blockers.append("transition_family_concentration")
        if concentration(easings) > 0.72:
            blockers.append("timing_easing_concentration")
        if concentration(durations) > 0.55:
            blockers.append("duration_repetition")
        if any("crawl" in motion for motion in motions):
            blockers.append("chart_crawl")
        variants[variant] = {
            "status": "PASS" if not blockers else "BLOCK",
            "blockers": blockers,
            "transition_family_concentration": round(concentration(transitions), 6),
            "timing_easing_concentration": round(concentration(easings), 6),
            "duration_concentration": round(concentration(durations), 6),
            "motion_intent_concentration": round(concentration(motions), 6),
            "longest_static_authored_run_seconds": longest_static,
            "longest_abstract_only_run_seconds": longest_abstract,
            "chart_crawl_detected": any("crawl" in motion for motion in motions),
            "must_use_asset_compliance": storyboard["variants"][variant]["must_use_asset_compliance"],
            "visual_mix": storyboard["variants"][variant]["visual_mix"],
            "segment_proxy_cache_keys": [
                row["cache_key"] for key, row in renders["segment_proxy_cache"].items() if key.startswith(variant + ":")
            ],
            "text_collision_and_safe_zone": "REQUIRES_RENDERED_CRITIC_AND_PIXEL_REVIEW",
            "chart_map_document_readability": "REQUIRES_RENDERED_CRITIC_AND_PHONE_SCALE_REVIEW",
        }
    report = {
        "schema_version": "contentops.retention_native.deterministic_temporal_qa.v2",
        "video_id": video_id,
        "variants": variants,
        "status": "PASS" if all(row["status"] == "PASS" for row in variants.values()) else "BLOCK",
        "machine_metrics_grant_aesthetic_acceptance": False,
        "public_write": False,
    }
    _write_json(runtime / "deterministic_media_qa.json", report)
    if report["status"] != "PASS":
        raise RuntimeError(f"deterministic_temporal_qa_block:{variants}")
    return report


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _validate_final_critic(text: str) -> tuple[bool, str | None, Any, str | None]:
    try:
        candidate = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        value = json.loads(candidate)
        if not isinstance(value, Mapping) or value.get("status") not in {
            "PASS", "PASS_WITH_NOTES", "REVISE", "BLOCK"
        }:
            raise ValueError("status")
        scope = value.get("scope")
        if (
            not isinstance(scope, Mapping)
            or scope.get("visual_images_reviewed") is not True
            or scope.get("actual_proxy_motion_sampled") is not True
            or scope.get("audio_listened") is not False
        ):
            raise ValueError("scope")
        issues = value.get("issues")
        if not isinstance(issues, list):
            raise ValueError("issues")
        for issue in issues:
            if not isinstance(issue, Mapping):
                raise ValueError("issue")
            if issue.get("severity") not in {"BLOCKER", "MAJOR", "MINOR", "NOTE"}:
                raise ValueError("severity")
            if issue.get("variant_id") not in {"short_9x16", "midform_16x9"}:
                raise ValueError("variant")
            if not str(issue.get("beat_id") or "").strip() or not str(issue.get("segment_id") or "").strip():
                raise ValueError("localization")
            if not isinstance(issue.get("start_seconds"), (int, float)) or not isinstance(issue.get("end_seconds"), (int, float)):
                raise ValueError("time")
            if float(issue["start_seconds"]) < 0 or float(issue["end_seconds"]) < float(issue["start_seconds"]):
                raise ValueError("time_order")
        material = any(issue["severity"] in {"BLOCKER", "MAJOR"} for issue in issues)
        if material != (value["status"] in {"REVISE", "BLOCK"}):
            raise ValueError("material_status")
        if not isinstance(value.get("summary"), str) or not isinstance(value.get("strengths"), list):
            raise ValueError("summary")
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return False, "structured_output_schema_invalid", None, f"final_critic_{exc}"
    return True, None, value, None


FINAL_CRITIC_PROMPT = """You are the independent senior temporal visual critic for a concrete-first financial-news proof. You did not author it. Inspect the labeled rendered captions-hidden proxy contact sheets and ordered motion strips for both separately composed formats, plus the 9:16 phone-scale still. Apply a demanding professional standard. Decide whether a normal viewer knows what they are looking at and can follow: oil + Hormuz, changed shipping/supply conditions, EIA forecast source, production/inventories/demand mechanism, price-is-not-proof boundary, and future confirmation points. Inspect unexplained abstraction, real-asset substitution, geographic clarity, chart/document readability, visual/narration alignment as represented by exact beat metadata, repeated movement, template feel, asset starvation, excessive text, caption dependence, hook/payoff, collision/overflow, source readability, chart crawl, and simultaneous unrelated motion. You cannot hear audio: review only supplied technical audio metrics and state that limitation.

Return ONLY JSON: {status:'PASS|PASS_WITH_NOTES|REVISE|BLOCK',summary:string,scope:{visual_images_reviewed:true,actual_proxy_motion_sampled:true,audio_listened:false,technical_audio_metrics_reviewed:true,limitations:[string]},issues:[{severity:'BLOCKER|MAJOR|MINOR|NOTE',variant_id:'short_9x16|midform_16x9',segment_id:string,beat_id:string,start_seconds:number,end_seconds:number,category:'hook|comprehension|grounding|map|chart|document|motion|layout|caption|audio|rights|evidence',observation:string,localized_fix:string}],strengths:[string],acceptance_recommendation:string}. Any BLOCKER/MAJOR requires REVISE or BLOCK. Localize each issue to exactly one segment and beat from the supplied timeline. Do not invent factual errors from thumbnails; report legibility/presentation defects precisely. PASS is evidence only, never owner acceptance."""


def run_final_critic(*, runtime: Path) -> dict[str, Any]:
    video_id = _runtime_video_id(runtime)
    review = _read_json(runtime / "review_media_manifest_v2.json")
    qa = _read_json(runtime / "deterministic_media_qa.json")
    segments = _read_json(runtime / "contracts" / "segment_authorship_v2.json")
    audio_path = runtime / "audio_mux_manifest_v2.json"
    audio = _read_json(audio_path) if audio_path.is_file() else {"status": "NOT_YET_AVAILABLE"}
    image_rows: list[tuple[str, Path]] = []
    for variant in ("short_9x16", "midform_16x9"):
        image_rows.append((f"{variant} captions-hidden proxy contact sheet", Path(review["variants"][variant]["contact_sheet"]["path"])))
        image_rows.append((f"{variant} ordered captions-hidden motion strip", Path(review["variants"][variant]["motion_strip"]["path"])))
    image_content: list[dict[str, Any]] = []
    for label, path in image_rows:
        image_content.extend((
            {"type": "text", "text": f"IMAGE LABEL: {label}"},
            {"type": "image_url", "image_url": {"url": _data_uri(path), "detail": "high"}},
        ))
    timeline: dict[str, list[dict[str, Any]]] = {}
    for variant in ("short_9x16", "midform_16x9"):
        at = 0.0
        rows: list[dict[str, Any]] = []
        for segment in segments["segments"]:
            for beat in segment[f"{variant}_beats"]:
                duration = float(beat["duration_seconds"])
                rows.append({
                    "segment_id": segment["segment_id"], "beat_id": beat["beat_id"],
                    "start_seconds": round(at, 3), "end_seconds": round(at + duration, 3),
                    "viewer_takeaway": beat["viewer_takeaway"],
                    "primary_visual_type": beat["primary_visual_type"],
                    "recognizable_subject": beat["recognizable_subject"],
                    "asset_ids": beat["asset_ids"], "motion_intent": beat["motion_intent"],
                    "transition_intent": beat["transition_intent"], "timing_easing": beat["timing_easing"],
                })
                at += duration
        timeline[variant] = rows
    technical = {
        "video_id": video_id,
        "timeline": timeline,
        "deterministic_qa": qa,
        "technical_audio": audio,
        "images": [{"label": label, "sha256": sha256_file(path)} for label, path in image_rows],
        "jim_chatgpt_acceptance": "PENDING",
        "public_write_authority": False,
    }

    def provider(prompt: str, model: str, timeout: float) -> ProviderResult:
        return call_nine_router_v2_isolated(
            [{"type": "text", "text": prompt + "\n\nTECHNICAL CONTEXT:\n" + json.dumps(technical, sort_keys=True)}, *image_content],
            model, timeout,
            role_task_id=ROLE_MULTIMODAL_VIDEO_CRITIC,
            logical_invocation_id=logical_invocation_id,
            component="CanonicalMultimodalCritic",
            max_tokens=7000, temperature=0.1,
        )

    logical_invocation_id = f"inv_v2_final_critic_{logical_hash(technical)[:20]}"
    invocation = routed_v2_isolated_invocation(
        prompt=FINAL_CRITIC_PROMPT,
        role_task_id=ROLE_MULTIMODAL_VIDEO_CRITIC,
        logical_invocation_id=logical_invocation_id,
        component="CanonicalMultimodalCritic",
        work_item_id=video_id,
        timeout_seconds=600.0,
        validator=_validate_final_critic,
        provider_call=provider,
        governed_input=technical,
        prompt_template="concrete_first_final_temporal_critic",
        prompt_version="v1",
    )
    if invocation.get("terminal_disposition") != ACCEPTED:
        raise RuntimeError(f"final_critic_router_blocked:{invocation.get('terminal_disposition')}")
    report = dict(invocation["output"])
    report.update({
        "schema_version": "contentops.retention_native.final_independent_critic.v2",
        "video_id": video_id,
        "critic_identity": {
            "route": ROLE_MULTIMODAL_VIDEO_CRITIC,
            "selected_model": invocation.get("selected_model"),
            "model_identity_note": invocation.get("model_identity_note"),
        },
        "router_evidence": {key: invocation.get(key) for key in (
            "logical_invocation_id", "terminal_disposition", "selected_model",
            "models_attempted_in_order", "total_attempts", "total_usage", "total_cost", "attempts",
        )},
        "independent_of_creative_authors": True,
        "owner_acceptance": "PENDING",
        "publication_authority": False,
        "public_write": False,
    })
    _write_json(runtime / "independent_critic_report_v2.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("artifacts", "qa", "critic"))
    parser.add_argument("--runtime", default=str(DEFAULT_RUNTIME))
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    runtime = Path(args.runtime).resolve()
    if args.stage == "artifacts":
        result = build_review_artifacts(runtime=runtime, ffmpeg=args.ffmpeg)
    elif args.stage == "qa":
        result = deterministic_qa(runtime=runtime)
    else:
        result = run_final_critic(runtime=runtime)
    print(json.dumps({"status": "PASS", "stage": args.stage, "result_sha256": logical_hash(result)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
