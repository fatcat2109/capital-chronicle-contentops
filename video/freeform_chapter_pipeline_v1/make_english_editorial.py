"""Materialize the canonical English package without editorial transformation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CHAPTER_TITLES = {
    "chapter_01": "Nine Days Later",
    "chapter_02": "The Rate That Fell Without Hiring",
    "chapter_03": "The Revolving Door Stopped",
    "chapter_04": "One Sector Holds the Ceiling",
    "chapter_05": "The Machine Keeps Running",
    "chapter_06": "The Missing Share",
    "chapter_07": "No Easy Exit",
}


def parse_strings(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    body = text.split("export const en = {", 1)[1].split("} as const;", 1)[0]
    return {
        match.group(1): match.group(2).replace("\\'", "'")
        for match in re.finditer(r"^\s*'([^']+)'\s*:\s*'((?:\\'|[^'])*)',?\s*$", body, re.M)
    }


def build(project: Path) -> dict[str, object]:
    strings = parse_strings(project / "src" / "strings.ts")
    narration = {
        path.stem: path.read_text(encoding="utf-8")
        for path in sorted((project.parent / "frozen_without_breaking_v1" / "narration").glob("chapter_*.txt"))
    }
    segments = [
        {"id": f"caption.{index:02d}", "text": strings[f"caption.{index:02d}"], "caption_text": strings[f"caption.{index:02d}"]}
        for index in range(1, 11)
    ]
    return {
        "schema": "contentops.v2.localized_editorial_package.v1",
        "language": "English",
        "locale": "en",
        "editor_receipt": {
            "model": "canonical-source-copy",
            "reasoning_effort": "none",
            "scope": "NO_LOCALIZATION_CANONICAL_ENGLISH_BYTES",
            "notes": ["Narration and viewer strings copied from governed authored source."],
        },
        "longform": {
            "title": "Frozen Without Breaking",
            "description": "Why employment, worker mobility, and aggregate output can tell different stories—and what would confirm a freeze, a thaw, or a break.",
            "social_copy": "The economy can keep moving while workers cannot. Frozen Without Breaking follows the labor-market arithmetic, the stopped revolving door, and the conditions that would change the diagnosis.",
            "chapter_titles": CHAPTER_TITLES,
            "narration_chapters": narration,
            "authority_captions": [
                {"id": "AUTH_COLD_OPEN", "text": "The economy is showing impressive resilience. Even with recent shocks, the trends are positive and reveal solid growth. Job gains have kept pace with the workforce, and the unemployment rate has changed little."},
                {"id": "AUTH_MID_FILM", "text": "I don't believe that either part of our mandate is generally at war with the other part. I do not believe that price stability and full employment is an either-or proposition. That isn't my judgment."},
            ],
        },
        "short": {
            "title": "How Jobs and Unemployment Both Fell",
            "description": "The arithmetic behind July's labor-market paradox—and why low hiring, low quitting, and low firing can feel frozen even while the economy keeps moving.",
            "social_copy": "Jobs fell. Unemployment fell. The contradiction resolves in the household-survey arithmetic—and the diagnosis is a low-hire, low-quit, low-fire freeze.",
            "hashtags": ["#LaborMarket", "#Economics", "#CapitalChronicle"],
            "strings": strings,
            "narration_segments": segments,
        },
        "anchor_assertions": [],
        "tts_guidance": {"voice_character": "controlled, intimate institutional narrator", "pronunciations": [], "known_risks": []},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--short-project", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build(args.short_project), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
