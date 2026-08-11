"""Focused tests for the Tier-2-B Remotion multimodal factory.

Pure-logic coverage: eligibility (including VIDEO_NOT_SELECTED), program
invariants, semantic-vs-execution hash separation, cache-key sensitivity,
assembly offset math, caption sidecar boundaries, and the revision whitelist.
No ffmpeg/node/provider calls are made here.
"""
from copy import deepcopy
from pathlib import Path

import pytest

from live_contentops import cli
from live_contentops import tier2_remotion_factory_v1 as b1
from live_contentops.tier2_video_factory_v1 import load_governed_input

INPUT = Path("docs/automation/CONTENTOPS_FULL_AUTOMATION_LIVE_CANONICAL_BROWSER_RUN_V1/contentops_full_automation_live_20260807_1")
DIRECTOR = {
    "director_version": "test-director",
    "hook_style": "level_first",
    "pacing": "measured",
    "chapter_emphasis": "term_structure",
    "short_angle": "quarter_compression",
}


def _story():
    return load_governed_input(INPUT)


def _programs():
    story = _story()
    series = b1.compute_curve_series(story)
    long_program = b1.build_long_program(story, series, DIRECTOR)
    short_program = b1.build_short_program(story, series, DIRECTOR)
    return story, series, long_program, short_program


def test_eligibility_selected_and_not_selected_truth_table():
    story = _story()
    selected = b1.decide_video_eligibility_b1(story)
    assert selected["result"] == "VIDEO_SELECTED"

    weak = b1.build_not_selected_case(b1.REPO_ROOT)
    not_selected = b1.decide_video_eligibility_b1(weak)
    assert not_selected["result"] == "VIDEO_NOT_SELECTED"
    assert not_selected["video_not_selected_is_success"] is True
    assert not_selected["reasons"]

    blocked = deepcopy(story)
    blocked["media_assets"] = [{**a, "rights_status": "unknown_rights"} for a in blocked["media_assets"]]
    assert b1.decide_video_eligibility_b1(blocked)["result"] == "VIDEO_BLOCKED"


def test_long_program_structure_and_claim_coverage():
    _, _, program, _ = _programs()
    scene_ids = [s["scene_id"] for s in program["scenes"]]
    assert len(scene_ids) == len(set(scene_ids))
    chapter_scene_refs = {sid for c in program["chapters"] for sid in c["scene_ids"]}
    assert chapter_scene_refs == set(scene_ids)
    assert {s["chapter_id"] for s in program["scenes"]} == {c["chapter_id"] for c in program["chapters"]}
    coverage = {b["claim_id"] for s in program["scenes"] for b in s["claim_bindings"]}
    assert coverage == set(b1.CLAIM_IDS)
    assert all(str(s["credits"]).startswith("Source:") for s in program["scenes"])
    assert all(s["narration_segments"] and all(seg for seg in s["narration_segments"]) for s in program["scenes"])
    assert program["public_write_authority"] is False


def test_short_program_independent_native_identity():
    _, _, long_program, short_program = _programs()
    long_ids = {s["scene_id"] for s in long_program["scenes"]}
    short_ids = {s["scene_id"] for s in short_program["scenes"]}
    assert long_ids.isdisjoint(short_ids)
    res = short_program["render_resolution"]
    assert res["width"] < res["height"]
    assert short_program["mode"] == "SHORT_FORM_NATIVE"


def test_semantic_program_hash_excludes_execution_state():
    _, _, program, _ = _programs()
    before = program["program_hash"]
    mutated = deepcopy(program)
    mutated["qa_state"] = "SOMETHING_ELSE"
    mutated["revision_state"] = "REVISED"
    assert b1._semantic_program_hash(mutated) == before
    mutated["scenes"][3]["script"] = "Different factual narration."
    assert b1._semantic_program_hash(mutated) != before


def _narration(scene_id):
    return {
        "provider": "kokoro",
        "voice": "af_heart",
        "speed": 1.0,
        "segments": [
            {"segment_id": f"{scene_id}-seg1", "audio_sha256": "aa" * 32, "duration_seconds": 10.0},
            {"segment_id": f"{scene_id}-seg2", "audio_sha256": "bb" * 32, "duration_seconds": 8.5},
        ],
    }


def _scene_fixture(scene_id="sc-1", chapter_id="ch-1"):
    return {
        "scene_id": scene_id,
        "chapter_id": chapter_id,
        "semantic_purpose": "purpose",
        "display_title": "Title",
        "kicker": "Kicker",
        "subtitle": None,
        "script": "Narration text.",
        "narration_segments": ["Narration text."],
        "claim_bindings": [{"claim_id": "UST:2Y:2026-07-13", "evidence_id": b1.SOURCE_ID, "source_url": b1.SOURCE_URL}],
        "source_bindings": [{"evidence_id": b1.SOURCE_ID, "source_url": b1.SOURCE_URL}],
        "visual_primitive": "TITLE_OPENING",
        "numbers": [],
        "series": [],
        "text_blocks": [],
        "asset_refs": ["asset-a"],
        "rights_requirements": {"status": "public_domain_source_and_local_render"},
        "credits": "Source: U.S. Department of the Treasury. Capital Chronicle render.",
        "motion_intent": "opening_title_reveal",
        "revision_history": [],
    }


def test_scene_cache_key_sensitivity_matrix():
    scene = _scene_fixture()
    narration = _narration("sc-1")
    assets = {"asset-a": "assets/deadbeef.png"}
    base = b1.scene_cache_key(scene, narration=narration, staged_assets=assets, width=1280, height=720, fps=24, renderer_version="remotion@4.0.507")

    title_change = deepcopy(scene)
    title_change["display_title"] = "Different Title"
    assert b1.scene_cache_key(title_change, narration=narration, staged_assets=assets, width=1280, height=720, fps=24, renderer_version="remotion@4.0.507") != base

    voice_change = dict(narration)
    voice_change["voice"] = "af_nova"
    assert b1.scene_cache_key(scene, narration=voice_change, staged_assets=assets, width=1280, height=720, fps=24, renderer_version="remotion@4.0.507") != base

    audio_change = deepcopy(narration)
    audio_change["segments"][0]["audio_sha256"] = "cc" * 32
    assert b1.scene_cache_key(scene, narration=audio_change, staged_assets=assets, width=1280, height=720, fps=24, renderer_version="remotion@4.0.507") != base

    asset_change = {"asset-a": "assets/otherhash.png"}
    assert b1.scene_cache_key(scene, narration=narration, staged_assets=asset_change, width=1280, height=720, fps=24, renderer_version="remotion@4.0.507") != base

    renderer_change = b1.scene_cache_key(scene, narration=narration, staged_assets=assets, width=1280, height=720, fps=24, renderer_version="remotion@9.9.9")
    assert renderer_change != base
    assert b1.scene_cache_key(scene, narration=narration, staged_assets=assets, width=1280, height=720, fps=24, renderer_version="remotion@4.0.507") == base

    other_scene = _scene_fixture(scene_id="sc-2")
    b1.scene_cache_key(other_scene, narration=_narration("sc-2"), staged_assets=assets, width=1280, height=720, fps=24, renderer_version="remotion@4.0.507")
    assert b1.scene_cache_key(scene, narration=narration, staged_assets=assets, width=1280, height=720, fps=24, renderer_version="remotion@4.0.507") == base


def test_chapter_cache_key_depends_on_scene_hashes_and_transition():
    chapter = {"chapter_id": "ch-1", "scene_ids": ["sc-1", "sc-2"]}
    rows = [
        {"scene_id": "sc-1", "render_sha256": "h1"},
        {"scene_id": "sc-2", "render_sha256": "h2"},
    ]
    base = b1.chapter_cache_key(chapter, rows, "remotion@4.0.507")
    rows_changed = [dict(rows[0]), {"scene_id": "sc-2", "render_sha256": "h2-changed"}]
    assert b1.chapter_cache_key(chapter, rows_changed, "remotion@4.0.507") != base
    other_chapter = {"chapter_id": "ch-2", "scene_ids": ["sc-1"]}
    b1.chapter_cache_key(other_chapter, [rows[0]], "remotion@4.0.507")
    assert b1.chapter_cache_key(chapter, rows, "remotion@4.0.507") == base


def test_assembly_offsets_and_caption_sidecar_boundaries(tmp_path: Path):
    _, _, program, _ = _programs()
    narration_by_scene = {s["scene_id"]: {"segments": [{"segment_id": f"{s['scene_id']}-seg{i + 1}", "audio_sha256": "x", "duration_seconds": 10.0, "text": seg_text} for i, seg_text in enumerate(s["narration_segments"])]} for s in program["scenes"]}
    scene_rows = [{"scene_id": s["scene_id"], "cache_key": f"key-{s['scene_id']}", "duration_seconds": 10.0 * len(s["narration_segments"]) + b1.TAIL_SECONDS} for s in program["scenes"]]
    cache = {row["cache_key"]: row for row in scene_rows}
    chapter_rows = [{"chapter_id": c["chapter_id"], "duration_seconds": sum(cache[f"key-{sid}"]["duration_seconds"] for idx, sid in enumerate(c["scene_ids"])) - (len(c["scene_ids"]) - 1) * b1.TRANSITION_FRAMES / b1.LONG_FPS} for c in program["chapters"]]
    assembly = b1.compute_assembly_offsets(chapter_rows, program, scene_rows, narration_by_scene, cache)
    assert assembly["expected_master_duration_seconds"] > 0
    # Scene starts are chapter-relative; each chapter's scene starts must be non-decreasing,
    # and chapter starts must be globally non-decreasing.
    by_chapter = {}
    for row in assembly["scenes"]:
        by_chapter.setdefault(row["chapter_id"], []).append(row["start_seconds"])
    for starts in by_chapter.values():
        assert starts == sorted(starts)
    chapter_starts = [row["start_seconds"] for row in assembly["chapters"]]
    assert chapter_starts == sorted(chapter_starts)

    package_root = tmp_path / "package"
    captions = b1.build_caption_sidecars(program, narration_by_scene, assembly, package_root, tag="long")
    total_segments = sum(len(v["segments"]) for v in narration_by_scene.values())
    assert captions["cue_count"] == total_segments
    srt = Path(captions["srt"]).read_text(encoding="utf-8")
    assert "-->" in srt
    assert Path(captions["vtt"]).is_file()


def test_bounded_revision_whitelist_never_touches_facts(tmp_path: Path):
    _, _, program, _ = _programs()
    before_scripts = {s["scene_id"]: s["script"] for s in program["scenes"]}
    before_numbers = {s["scene_id"]: deepcopy(s["numbers"]) for s in program["scenes"]}
    before_claims = {s["scene_id"]: deepcopy(s["claim_bindings"]) for s in program["scenes"]}
    critic = {"status": "CRITIC_NEEDS_REVISION", "defects": [
        {"class": "headline_typography_clipping", "severity": "high", "confidence": "high", "evidence": "frame sample", "target": "scene"},
    ]}
    program_for_revision = deepcopy(program)
    for scene in program_for_revision["scenes"]:
        scene["display_title"] = "A VERY LONG DISPLAY TITLE THAT WILL CERTAINLY CLIP THE SAFE ZONE"
    result = b1.apply_bounded_revision(critic, program_for_revision, 1, tmp_path)
    assert result["applied"] in (True, False)
    for scene in program_for_revision["scenes"]:
        assert scene["script"] == before_scripts[scene["scene_id"]]
        assert scene["numbers"] == before_numbers[scene["scene_id"]]
        assert scene["claim_bindings"] == before_claims[scene["scene_id"]]
    over_budget = b1.apply_bounded_revision(critic, program_for_revision, b1.MAX_REVISION_ROUNDS + 1, tmp_path)
    assert over_budget["applied"] is False
    assert over_budget["reason"] == "revision_budget_exhausted"


def test_segment_split_preserves_text():
    text = "One. Two. Three. Four. Five. Six."
    parts = b1._segment_split(text, 3)
    assert len(parts) == 3
    assert " ".join(parts).replace("  ", " ").strip() == "One. Two. Three. Four. Five. Six."


def test_cli_registers_tier2_remotion_command():
    assert cli.COMMANDS["tier2-video-remotion"] is not None


def test_multimodal_critic_fails_closed_when_provider_disabled(tmp_path: Path, monkeypatch):
    _, _, program, _ = _programs()
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    fake_frame = frames_dir / "frame_000001.jpg"
    fake_frame.write_bytes(b"\xff\xd8\xff\xdb")
    monkeypatch.setattr(b1, "_media_facts", lambda path: {"duration_seconds": 900.0})
    monkeypatch.setattr(b1, "extract_representative_frames", lambda master_path, frames, out_dir: [fake_frame for _ in frames])
    monkeypatch.setattr(b1, "_downscale", lambda frame, out_dir, max_side=768: frame)
    result = b1.run_multimodal_critic(tmp_path / "master.mp4", program, tmp_path, provider_enabled=False)
    assert result["status"] == "CRITIC_PROVIDER_DISABLED_AWAITING_HUMAN"
    assert result["provider_used"] is False
    assert result["defects"] == []


def test_multimodal_critic_rejects_non_factual_scope(tmp_path: Path, monkeypatch):
    """A critic result must never be treated as factual authority; malformed output escalates."""
    _, _, program, _ = _programs()
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    fake_frame = frames_dir / "frame_000001.jpg"
    fake_frame.write_bytes(b"\xff\xd8\xff\xdb")
    monkeypatch.setattr(b1, "_media_facts", lambda path: {"duration_seconds": 900.0})
    monkeypatch.setattr(b1, "extract_representative_frames", lambda master_path, frames, out_dir: [fake_frame for _ in frames])
    monkeypatch.setattr(b1, "_downscale", lambda frame, out_dir, max_side=768: frame)

    class _FakeResult:
        text = "this is not json at all"
        usage = None
        provider_invocation_id = "inv_test"
        cost = None

    result = b1.run_multimodal_critic(
        tmp_path / "master.mp4", program, tmp_path, provider_enabled=True,
        critic_provider_call=lambda text, imgs, model: _FakeResult(),
    )
    assert result["status"] == "CRITIC_OUTPUT_MALFORMED_ESCALATE"
    assert result["defects"] == []

