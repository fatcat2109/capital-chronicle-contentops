from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

from live_contentops.short_longform_low_cost_audio_v1 import (
    CHATTERBOX_CANDIDATE, KOKORO_BUILD, PARLER_CANDIDATE, FormatAudioLedger,
    build_missing_segment_request, segment_cache_key, validate_format_contract,
    validate_zero_write,
)

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "run_v2_short_longform_low_cost_audio_v1.py"


def load_script():
    spec = importlib.util.spec_from_file_location("short_longform_runner", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_formats_are_independently_authored_and_longform_is_substantive():
    module = load_script()
    result = validate_format_contract(module.SHORT_SCENES, module.LONG_SCENES)
    assert result["status"] == "PASS"
    assert len(module.SHORT_SCENES) == 8
    assert len(module.LONG_SCENES) == 18
    assert len(" ".join(row["narration"] for row in module.LONG_SCENES).split()) >= 850
    assert not any("midform" in row["scene_id"].lower() for row in module.LONG_SCENES)


def test_audio_cache_is_immutable_and_only_missing_segments_are_requested(tmp_path: Path):
    scenes = [{"scene_id": "A", "narration": "A precise sentence."}, {"scene_id": "B", "narration": "Another precise sentence."}]
    request, rows = build_missing_segment_request(scenes, tmp_path)
    assert len(request["segments"]) == 2
    first = Path(rows[0]["path"])
    first.write_bytes(b"RIFF-cache-proof")
    request2, rows2 = build_missing_segment_request(scenes, tmp_path)
    assert len(request2["segments"]) == 1
    assert rows2[0]["status"] == "REUSED"
    assert segment_cache_key(scenes[0]["narration"], KOKORO_BUILD, {"speed": 1.0, "sample_rate": 24000}) == rows2[0]["cache_key"]


def test_audio_backend_policy_is_local_zero_cost_no_clone():
    KOKORO_BUILD.validate()
    assert KOKORO_BUILD.enabled_for_build
    assert KOKORO_BUILD.marginal_api_cost_usd == 0
    assert not KOKORO_BUILD.reference_audio_allowed
    assert not PARLER_CANDIDATE.enabled_for_build
    assert not CHATTERBOX_CANDIDATE.enabled_for_build


def test_ledger_reuses_identical_checkpoint_and_rejects_regression(tmp_path: Path):
    ledger = FormatAudioLedger(tmp_path / "ledger.sqlite3")
    ledger.create_job("job", "candidate")
    first = ledger.checkpoint("job", "STORY_LOCKED", {"a": 1}, {"b": 2})
    second = ledger.checkpoint("job", "STORY_LOCKED", {"a": 1}, {"b": 2})
    assert first["status"] == "WRITTEN" and second["status"] == "REUSED"
    ledger.checkpoint("job", "EVIDENCE_LOCKED", {"b": 2}, {"c": 3})
    with pytest.raises(ValueError, match="stage_regression"):
        ledger.checkpoint("job", "STORY_LOCKED", {}, {})
    ledger.close()


def test_creative_source_has_distinct_compositions_and_concrete_visuals():
    source = (REPO / "video" / "asset_first_v1" / "src" / "generated" / "treasuryPositioning.tsx").read_text(encoding="utf-8")
    root = (REPO / "video" / "asset_first_v1" / "src" / "root.tsx").read_text(encoding="utf-8")
    for token in ("TreasuryPositioningShort", "TreasuryPositioningLongform", "PositionBars", "DocumentRow", "RepoChain", "FlowChain", "Timeline", "Tests"):
        assert token in source or token in root
    assert "CODEX_VIEWER_FACING_AUTHORSHIP" in source
    assert "fetch(" not in source and "process.env" not in source


def test_speech_timing_drives_compositions_and_clean_audio_is_rendered():
    root = (REPO / "video" / "asset_first_v1" / "src" / "root.tsx").read_text(encoding="utf-8")
    renderer = (REPO / "video" / "asset_first_v1" / "scripts" / "render.mjs").read_text(encoding="utf-8")
    assert "props.scenes.reduce" in root
    assert "muted:false" in renderer
    assert "atempo" not in renderer


def test_caption_and_source_surfaces_are_separate():
    source = (REPO / "video" / "asset_first_v1" / "src" / "generated" / "treasuryPositioning.tsx").read_text(encoding="utf-8")
    assert "captionsVisible" in source
    assert "<Source" in source
    assert "sidecar" in SCRIPT.read_text(encoding="utf-8") or "captions" in SCRIPT.read_text(encoding="utf-8")


def test_zero_write_gate_covers_all_forbidden_surfaces():
    clean = {"public_writes": 0, "uploads": 0, "browser_profile_uses": 0, "elevenlabs_calls": 0, "v1_mutations": 0}
    assert validate_zero_write(clean)["status"] == "PASS"
    dirty = dict(clean, elevenlabs_calls=1)
    assert validate_zero_write(dirty)["status"] == "FAIL"


def test_runtime_handoff_if_present_has_real_media_contract():
    handoff = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_short_longform_low_cost_audio_20260815\HANDOFF.json")
    if not handoff.is_file():
        pytest.skip("runtime proof not present")
    data = json.loads(handoff.read_text(encoding="utf-8"))
    assert data["result"] == "PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW"
    short_stream = next(row for row in data["short"]["probe"]["streams"] if row["codec_type"] == "video")
    long_stream = next(row for row in data["longform"]["probe"]["streams"] if row["codec_type"] == "video")
    assert (short_stream["width"], short_stream["height"]) == (2160, 3840)
    assert (long_stream["width"], long_stream["height"]) == (1920, 1080)
    for stream in (short_stream, long_stream):
        assert stream["pix_fmt"] == "yuv420p"
        assert stream["color_range"] == "tv"
        assert stream["color_space"] == stream["color_transfer"] == stream["color_primaries"] == "bt709"
    assert 30 <= float(data["short"]["probe"]["format"]["duration"]) <= 60
    assert 300 <= float(data["longform"]["probe"]["format"]["duration"]) <= 2700
    assert data["safety"]["validation"]["status"] == "PASS"


def test_runtime_recovery_diversity_and_chapter_identity_if_present():
    root = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_short_longform_low_cost_audio_20260815")
    if not (root / "HANDOFF.json").is_file():
        pytest.skip("runtime proof not present")
    recovery = json.loads((root / "receipts" / "recovery_proof.json").read_text(encoding="utf-8"))
    assert recovery["audio_cache_rerun"] == {"status": "PASS", "generated": 0, "reused": 26}
    assert recovery["unaffected_masters_unchanged"]
    chapters = json.loads((root / "contracts" / "longform_chapter_hashes.json").read_text(encoding="utf-8"))
    assert len(chapters) == len(set(chapters.values())) == 18
    dependencies = json.loads((root / "contracts" / "render_dependency_manifest.json").read_text(encoding="utf-8"))
    assert len(dependencies["families"]) >= 6
    assert dependencies["external_runtime_fetches"] == 0


def test_runtime_sidecar_captions_are_compact_if_present():
    root = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_short_longform_low_cost_audio_20260815\captions")
    if not root.is_dir():
        pytest.skip("runtime proof not present")
    def seconds(value: str) -> float:
        return int(value[:2]) * 3600 + int(value[3:5]) * 60 + int(value[6:8]) + int(value[9:]) / 1000
    for path in root.glob("*.srt"):
        text = path.read_text(encoding="utf-8")
        durations = [seconds(end) - seconds(start) for start, end in re.findall(r"(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})", text)]
        assert durations and min(durations) >= 1.9 and max(durations) <= 4.0
