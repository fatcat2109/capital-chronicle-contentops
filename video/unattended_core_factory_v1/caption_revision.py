"""Caption layout revision on a sealed private package, without picture/audio work."""

from __future__ import annotations

import copy
import json
import textwrap
from pathlib import Path

from video.freeform_chapter_pipeline_v1.package_factory import (
    build_publication_package,
    validate_caption_set,
    write_caption_artifacts,
)

from .creative import hash_file


def revise_caption_layout(package_path: Path, output_dir: Path, *, width: int = 32):
    """Bind a successor package through the canonical package owner.

    Only whitespace layout changes. Transcript, timings, audio and picture remain
    exact. A distinct directory makes changed caption identities reviewable and
    prevents mutation of the accepted package or an older revision.
    """
    if not 24 <= width <= 48:
        raise ValueError("Caption width must be24..48")
    original = json.loads(package_path.read_text(encoding="utf-8"))
    for item in original["artifacts"].values():
        if item is not None and hash_file(item["path"]) != item["sha256"]:
            raise ValueError("Original package artifact drift")
    if output_dir.exists():
        raise ValueError("Use a distinct caption revision directory")
    captions = json.loads(
        Path(original["artifacts"]["caption_json"]["path"]).read_text(encoding="utf-8")
    )
    changed = copy.deepcopy(captions)
    for cue in changed["cues"]:
        cue["text"] = textwrap.fill(
            " ".join(cue["text"].split()),
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
    if changed == captions:
        raise ValueError("Caption revision contains no layout change")
    if not all(
        a["text"].split() == b["text"].split()
        for a, b in zip(captions["cues"], changed["cues"])
    ):
        raise ValueError("Caption revision changed spoken words")
    if validate_caption_set(changed)["result"] != "PASS_CAPTIONS":
        raise ValueError("Invalid revised captions")
    artifacts = write_caption_artifacts(changed, output_dir / "captions")
    spec = {
        k: v
        for k, v in original.items()
        if k
        not in {
            "artifacts",
            "package_id",
            "generation_timestamp_utc",
            "transport",
            "publication_state",
        }
    }
    for key in ("canonical_picture", "burned_caption_video", "audio"):
        item = original["artifacts"][key]
        spec[key] = item["path"] if item else None
    for key in ("json", "srt", "vtt"):
        spec["caption_" + key] = artifacts[key]["path"]
    spec["generation_version"] = "caption-layout-" + str(width)
    successor = build_publication_package(spec)
    for key in (
        "canonical_transcript_identity",
        "canonical_transcript_hash",
        "narration_timing_lock_hash",
        "voiceover_qa_hash",
        "seo_derivation",
        "seo_package_hash",
        "governed_input_hash",
        "final_mux",
        "final_audio",
    ):
        if key in original:
            successor[key] = original[key]
    manifest = output_dir / "platform_neutral_package_manifest.json"
    manifest.write_text(json.dumps(successor, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "result": "PRIVATE_CAPTION_LAYOUT_REVISION_BUILT",
        "parent_package_id": original["package_id"],
        "package_id": successor["package_id"],
        "source_package_sha256": hash_file(package_path),
        "picture_sha256": successor["artifacts"]["canonical_picture"]["sha256"],
        "audio_sha256": successor["artifacts"]["audio"]["sha256"],
        "caption_sha256_before": original["artifacts"]["caption_json"]["sha256"],
        "caption_sha256_after": successor["artifacts"]["caption_json"]["sha256"],
        "picture_render_count": 0,
        "audio_synthesis_count": 0,
        "timings_and_words_unchanged": True,
        "quality_review": "REQUIRED",
        "public_write_authority": False,
        "manifest": str(manifest),
    }
    (output_dir / "reuse_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt
