"""Validate the bounded Retail Sales owner-repair runtime evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.breaking_news_crisp_v1 import (
    BANNED_VOICE_IDS,
    codex_execution_plane_manifest,
    sha256_file,
    validate_annotation_geometry,
    validate_audio_contract,
    validate_microbeat_timeline,
    validate_zero_public_write,
)


DEFAULT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_breaking_retail_owner_repair_20260815")


def read_json(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError(path)
    return value


def validate(runtime: Path) -> dict[str, Any]:
    errors: list[str] = []
    geometry=read_json(runtime/"contracts"/"document_geometry.json")
    audio=read_json(runtime/"contracts"/"audio_contract.json")
    timeline=read_json(runtime/"contracts"/"microbeat_timeline.json")
    crisp=read_json(runtime/"contracts"/"crisp_master.json")
    public_write=read_json(runtime/"contracts"/"zero_public_write.json")
    baseline=read_json(runtime/"contracts"/"document_before_baseline.json")
    delivery_frames=read_json(runtime/"contracts"/"document_delivery_frames.json")

    gates={
        "annotation_geometry":validate_annotation_geometry(geometry),
        "audio_contract":validate_audio_contract(audio),
        "microbeat_timeline":validate_microbeat_timeline(timeline),
        "zero_public_write":validate_zero_public_write(public_write),
        "master_4k":crisp["master"]["gate"],
        "derivative_1080":crisp["derivative"]["gate"],
    }
    for name,gate in gates.items():
        if gate.get("status") != "PASS":
            errors.append(f"gate_failed:{name}:{gate.get('errors')}")

    if audio.get("voice_id") in BANNED_VOICE_IDS:
        errors.append("banned_voice_selected")
    if any(row.get("voice_id") in BANNED_VOICE_IDS for row in audio.get("segments", [])):
        errors.append("banned_voice_used_in_segment")
    if audio.get("global_atempo_used") is not False:
        errors.append("global_atempo_used")
    measurement=audio.get("measurement", {})
    if not -17.0 <= float(measurement.get("integrated_lufs", 0)) <= -15.0:
        errors.append("master_loudness_outside_gate")
    if float(measurement.get("true_peak_dbtp", 0)) > -1.0:
        errors.append("master_true_peak_outside_gate")

    captions=Path(audio["sidecar_caption"]["path"])
    if not captions.is_file() or sha256_file(captions) != audio["sidecar_caption"]["sha256"]:
        errors.append("caption_sidecar_missing_or_changed")
    if crisp.get("proxy_lineage") is not False:
        errors.append("proxy_lineage")
    for key in ("master","derivative"):
        media=Path(crisp[key]["path"])
        if not media.is_file() or sha256_file(media) != crisp[key]["sha256"]:
            errors.append(f"media_missing_or_changed:{key}")

    before_sizes={}
    for row in baseline["frames"]:
        with Image.open(row["screenshot"]) as image:
            before_sizes[row["label"]]=list(image.size)
    after_sizes={}
    for row in delivery_frames["delivery_extracts"]:
        with Image.open(row["screenshot"]) as image:
            after_sizes[row["label"]]=list(image.size)
        if row["media_sha256"] not in {crisp["master"]["sha256"],crisp["derivative"]["sha256"]}:
            errors.append(f"delivery_frame_wrong_media:{row['label']}")
    expected={"1080x1920":[1080,1920],"2160x3840":[2160,3840]}
    if before_sizes != expected or after_sizes != expected:
        errors.append("before_after_frame_dimensions")

    execution=codex_execution_plane_manifest()
    if execution["nine_router_route"] is not None:
        errors.append("nine_router_route_not_null")

    result={
        "status":"PASS" if not errors else "FAIL",
        "errors":errors,
        "gates":gates,
        "voice":{"selected_voice_id":audio["voice_id"],"banned_voice_ids":sorted(BANNED_VOICE_IDS),"segment_count":len(audio["segments"])},
        "audio_measurement":measurement,
        "media":{"master":crisp["master"],"derivative":crisp["derivative"],"proxy_lineage":crisp["proxy_lineage"]},
        "frames":{"before_sizes":before_sizes,"after_sizes":after_sizes},
        "captions":{"path":str(captions),"sha256":sha256_file(captions)},
        "codex_execution_plane":execution,
        "safety":{"v1_mutations":0,"uploads":0,"browser_publication_calls":0,"mode_bakeoff_runs":0,"v2_02_runs":0},
    }
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser=argparse.ArgumentParser()
    parser.add_argument("--runtime",type=Path,default=DEFAULT_RUNTIME)
    parser.add_argument("--output",type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args=parse_args(argv);result=validate(args.runtime.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
