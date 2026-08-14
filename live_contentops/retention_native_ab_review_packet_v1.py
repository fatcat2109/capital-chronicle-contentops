"""Build the owner-facing A/B packet for the two isolated V2 video lanes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops.retention_native_concrete_first_v2 import canonical_json, logical_hash

SCHEMA_VERSION = "contentops.retention_native.ab_review_packet.v1"


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def _lane_summary(root: Path, *, lane_id: str, brain: dict[str, Any]) -> dict[str, Any]:
    probe = _read(root / "final_media_probe_v2.json")
    audio = _read(root / "audio_mux_manifest_v2.json")
    critic = _read(root / "independent_critic_report_v2.json")
    review = _read(root / "review_media_manifest_v2.json")
    motion = _read(root / "motion_render_manifest_v2.json")
    video_id = str(motion["video_id"])
    identities = {
        str(row.get("video_id") or "")
        for row in (probe, audio, critic, review, motion)
    }
    if identities != {video_id}:
        raise RuntimeError(f"lane_video_id_mismatch:{lane_id}:{sorted(identities)}")
    if probe.get("status") != "PASS":
        raise RuntimeError(f"lane_probe_not_pass:{lane_id}")
    if critic.get("status") not in {"PASS", "PASS_WITH_NOTES"}:
        raise RuntimeError(f"lane_critic_not_accepted:{lane_id}:{critic.get('status')}")

    variants: dict[str, Any] = {}
    for variant in ("short_9x16", "midform_16x9"):
        rendered = probe["variants"][variant]
        sound = audio["variants"][variant]
        variants[variant] = {
            "duration_seconds": rendered["final"]["duration_seconds"],
            "resolution": [rendered["final"]["width"], rendered["final"]["height"]],
            "fps": rendered["final"]["fps"],
            "video_codec": rendered["final"]["video_codec"],
            "audio_codec": rendered["final"]["audio_codec"],
            "final": {
                key: rendered["final"][key]
                for key in ("path", "sha256", "size_bytes", "status")
            },
            "captions_hidden": {
                key: rendered["captions_hidden"][key]
                for key in ("path", "sha256", "size_bytes", "status")
            },
            "audio": {
                "tts_provider": sound["narration"]["provider"],
                "tts_model": sound["narration"]["model"],
                "voice": sound["narration"]["voice"],
                "integrated_lufs": sound["master"]["measurement"]["integrated_lufs"],
                "true_peak_dbtp": sound["master"]["measurement"]["true_peak_dbtp"],
                "score_rights_status": sound["score"]["rights_status"],
                "score_generator": sound["score"]["generator"],
                "executed_sfx_cue_count": sound["score"]["executed_sfx_cue_count"],
            },
            "contact_sheet": review["variants"][variant]["contact_sheet"]["path"],
            "motion_strip": review["variants"][variant]["motion_strip"]["path"],
        }
    return {
        "lane_id": lane_id,
        "runtime": str(root),
        "video_id": video_id,
        "brain": brain,
        "motion_authorship_sha256": motion["authorship_sha256"],
        "variants": variants,
        "critic": {
            "status": critic["status"],
            "summary": critic["summary"],
            "issues": critic["issues"],
            "strengths": critic["strengths"],
            "selected_model": critic["critic_identity"]["selected_model"],
            "report_path": str(root / "independent_critic_report_v2.json"),
        },
        "public_write": False,
    }


def _markdown(packet: dict[str, Any]) -> str:
    a = packet["lanes"]["lane_a_9router_cx_xhigh"]
    b = packet["lanes"]["lane_b_codex_builder"]
    lines = [
        "# Capital Chronicle V2 — A/B owner review packet",
        "",
        "Status: READY_FOR_JIM_REVIEW. No public write or upload occurred.",
        "",
        "## Fair comparison contract",
        "",
        "Both lanes use the same governed Hormuz/EIA benchmark, the same short and midform durations, the same aspect ratios, and the same documentary asset universe. The creative brain is the controlled variable.",
        "",
        "| Lane | Creative brain | Critic | Short | Midform |",
        "|---|---|---|---|---|",
        f"| A | CX GPT-5.6 SOL xhigh through 9Router | {a['critic']['status']} | {a['variants']['short_9x16']['final']['path']} | {a['variants']['midform_16x9']['final']['path']} |",
        f"| B | Codex Builder; V2 tools only for waveform/render | {b['critic']['status']} | {b['variants']['short_9x16']['final']['path']} | {b['variants']['midform_16x9']['final']['path']} |",
        "",
        "## Review order",
        "",
        "1. Watch both shorts once without pausing; score the first three seconds and overall urge to continue.",
        "2. Watch both midforms without captions; score comprehension and pacing.",
        "3. Rewatch with captions; score evidence clarity, visual craft, brand fit, and audio polish.",
        "4. Record one winner per format, then an overall production-lane decision.",
        "",
        "## Jim rubric (1–5)",
        "",
        "Hook/first 3s; comprehension without captions; purposeful visual density; pacing/retention; brand distinctiveness; trust/evidence boundaries; voice/music/SFX; replay/share potential; production operability.",
        "",
        "## Preliminary builder observations (not owner acceptance)",
        "",
        "Lane A is more granular and data-dense, with stronger model-authored per-segment variation. Lane B has larger brand hierarchy, a clearer physical-chain sequence, and a more distinctive editorial visual language. The final winner remains PENDING_JIM_REVIEW.",
        "",
        "## Evidence",
        "",
        f"Lane A contact sheets: {a['variants']['short_9x16']['contact_sheet']} ; {a['variants']['midform_16x9']['contact_sheet']}",
        f"Lane B contact sheets: {b['variants']['short_9x16']['contact_sheet']} ; {b['variants']['midform_16x9']['contact_sheet']}",
        f"Machine-readable packet: {packet['packet_json_path']}",
        "",
    ]
    return "\n".join(lines)


def build_review_packet(*, lane_a: Path, lane_b: Path, output_root: Path) -> dict[str, Any]:
    a = _lane_summary(
        lane_a,
        lane_id="lane_a_9router_cx_xhigh",
        brain={
            "creative_authority": "NINE_ROUTER_CX_GPT56_SOL_XHIGH",
            "requested_model": "cx/gpt-5.6-sol(xhigh)",
            "wire_model": "cx/gpt-5.6-sol",
            "reasoning_effort": "xhigh",
            "roles": ["V2_CREATIVE_EDITOR", "V2_MOTION_CODE_AUTHOR", "V2_CREATIVE_REVISION_AUTHOR"],
            "degraded_creative_model": False,
        },
    )
    capabilities = _read(lane_b / "codex_builder_capabilities_v1.json")
    b = _lane_summary(
        lane_b,
        lane_id="lane_b_codex_builder",
        brain={
            "creative_authority": "CODEX_BUILDER",
            "capability_split": capabilities["capabilities"],
            "generated_illustration": capabilities["generated_illustration"],
        },
    )
    for variant in ("short_9x16", "midform_16x9"):
        if a["variants"][variant]["duration_seconds"] != b["variants"][variant]["duration_seconds"]:
            raise RuntimeError(f"ab_duration_mismatch:{variant}")
        if a["variants"][variant]["resolution"] != b["variants"][variant]["resolution"]:
            raise RuntimeError(f"ab_resolution_mismatch:{variant}")

    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / "capital_chronicle_v2_ab_review_packet_v1.json"
    markdown_path = output_root / "capital_chronicle_v2_ab_review_packet_v1.md"
    packet: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "READY_FOR_JIM_REVIEW",
        "comparison_contract": {
            "same_governed_story": True,
            "same_documentary_asset_universe": True,
            "same_durations_and_formats": True,
            "controlled_variable": "CREATIVE_BRAIN_AND_AUTHORING_WORKFLOW",
        },
        "lanes": {a["lane_id"]: a, b["lane_id"]: b},
        "lane_b_revision_history": {
            "initial_critic_status": "REVISE",
            "initial_material_issues": [
                "clipped native chokepoint legend in short map split",
                "clipped native chokepoint legend in midform map split",
            ],
            "final_critic_status": b["critic"]["status"],
            "material_issues_remaining": False,
        },
        "jim_rubric": [
            "hook_first_3_seconds", "comprehension_without_captions",
            "purposeful_visual_density", "pacing_and_retention",
            "brand_distinctiveness", "trust_and_evidence_boundaries",
            "voice_music_sfx", "replay_share_potential", "production_operability",
        ],
        "preliminary_builder_observation": {
            "lane_a": "More granular and data-dense with model-authored per-segment variation.",
            "lane_b": "Larger brand hierarchy, clearer physical-chain sequence, and more distinctive editorial visual language.",
            "winner": "PENDING_JIM_REVIEW",
        },
        "owner_acceptance": "PENDING_JIM_REVIEW",
        "uploads": 0,
        "public_write": False,
        "packet_json_path": str(json_path),
        "packet_markdown_path": str(markdown_path),
    }
    packet["packet_content_sha256"] = logical_hash(packet)
    json_path.write_text(canonical_json(packet), encoding="utf-8")
    markdown_path.write_text(_markdown(packet), encoding="utf-8")
    return packet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane-a", required=True)
    parser.add_argument("--lane-b", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    packet = build_review_packet(
        lane_a=Path(args.lane_a).resolve(),
        lane_b=Path(args.lane_b).resolve(),
        output_root=Path(args.output_root).resolve(),
    )
    print(canonical_json({"status": packet["status"], "sha256": packet["packet_content_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
