"""Materialize governed locale strings and measured caption timings for Remotion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def typescript(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2).replace("</", "<\\/")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--locale-dir", type=Path, required=True)
    parser.add_argument("--audio-root", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()
    string_maps: dict[str, object] = {}
    timing_maps: dict[str, object] = {}
    for editorial_path in sorted(args.locale_dir.glob("*.json")):
        editorial = json.loads(editorial_path.read_text(encoding="utf-8"))
        locale = str(editorial["locale"])
        if locale != "en":
            string_maps[locale] = editorial["short"]["strings"]
        receipt_path = args.audio_root / locale / "audio_receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        cues = []
        for segment in receipt["short"]["segments"]:
            start = round(float(segment["timeline_start_seconds"]) * 30)
            end = round((float(segment["timeline_start_seconds"]) + float(segment["actual_audio_duration_seconds"])) * 30)
            cues.append({"from": start, "to": min(1740, end), "key": segment["cue_id"]})
        timing_maps[locale] = cues
    args.source_dir.mkdir(parents=True, exist_ok=True)
    (args.source_dir / "generated_locale_strings.ts").write_text(
        "// Generated deterministically from governed editorial locale JSON. Do not hand-edit.\n"
        f"export const localizedStringMaps: Record<string, Record<string, string>> = {typescript(string_maps)};\n",
        encoding="utf-8",
    )
    (args.source_dir / "generated_caption_timings.ts").write_text(
        "// Generated deterministically from measured local narration durations. Do not hand-edit.\n"
        "export const localizedCaptionCues: Record<string, Array<{from: number; to: number; key: string; emphasis?: string}>> = "
        f"{typescript(timing_maps)};\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
